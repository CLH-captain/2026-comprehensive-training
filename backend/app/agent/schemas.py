from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HermesReply:
    content: str
    model: str
    adapter: str = "hermes_cli"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeStatus:
    runtime_available: bool
    dashboard_available: bool
    ollama_available: bool
    model_available: bool
    model: str
    hermes_version: str | None = None

    @property
    def ready(self) -> bool:
        return self.runtime_available and self.ollama_available and self.model_available

    def as_dict(self) -> dict[str, bool | str | None]:
        return {"ready": self.ready, **asdict(self)}