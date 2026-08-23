from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

PLUGIN_DIR = Path(__file__).parents[3] / "hermes_plugin" / "szut-club-statistics"


@pytest.fixture(scope="module")
def plugin() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "szut_club_statistics",
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_plugin_registers_exactly_seven_strict_tools(plugin: ModuleType) -> None:
    registrations = []

    class Context:
        def register_tool(self, **kwargs) -> None:
            registrations.append(kwargs)

    plugin.register(Context())
    assert len(registrations) == 7
    assert {item["name"] for item in registrations} == set(plugin.TOOL_SCHEMAS)
    for item in registrations:
        assert item["toolset"] == "szut_club_statistics"
        assert item["schema"]["parameters"]["additionalProperties"] is False


def test_plugin_schema_constrains_dimensions_metrics_and_limits(plugin: ModuleType) -> None:
    schemas = plugin.TOOL_SCHEMAS
    distribution = schemas["get_distribution_statistics"]["parameters"]
    club_ranking = schemas["get_club_ranking"]["parameters"]["properties"]
    activity_ranking = schemas["get_activity_ranking"]["parameters"]["properties"]
    assert distribution["required"] == ["dimension"]
    assert distribution["properties"]["dimension"]["enum"] == ["category", "college", "campus"]
    assert club_ranking["metric"]["enum"] == ["activity_score"]
    assert activity_ranking["metric"]["enum"] == ["participant_times"]
    assert activity_ranking["limit"]["maximum"] == 50


def test_client_requires_internal_credentials(plugin: ModuleType, monkeypatch) -> None:
    monkeypatch.delenv("AGENT_INTERNAL_KEY", raising=False)
    monkeypatch.delenv("SZUT_AGENT_CONTEXT_TOKEN", raising=False)
    client_module = sys.modules[f"{plugin.__name__}.client"]
    with pytest.raises(RuntimeError, match="credentials"):
        client_module.ToolClient.from_env()


def test_tool_handler_returns_structured_success(plugin: ModuleType, monkeypatch) -> None:
    tools = sys.modules[f"{plugin.__name__}.tools"]

    class Client:
        def call(self, endpoint, payload):
            assert endpoint == "overview"
            assert payload == {"term_id": 2}
            return {"activity_count": 10}

    monkeypatch.setattr(tools.ToolClient, "from_env", lambda: Client())
    result = json.loads(tools.invoke("get_overview_statistics", {"term_id": 2}))
    assert result == {"success": True, "data": {"activity_count": 10}}