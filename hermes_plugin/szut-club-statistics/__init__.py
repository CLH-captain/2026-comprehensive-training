# ruff: noqa: N999
from __future__ import annotations

from .schemas import TOOL_SCHEMAS
from .tools import handler_for


def register(ctx) -> None:
    for name, schema in TOOL_SCHEMAS.items():
        ctx.register_tool(
            name=name,
            toolset="szut_club_statistics",
            schema=schema,
            handler=handler_for(name),
            emoji="📊",
        )
