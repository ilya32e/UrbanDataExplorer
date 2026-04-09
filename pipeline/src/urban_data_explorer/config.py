from dataclasses import dataclass
from typing import Any
import tomllib

from .paths import repo_path


@dataclass(frozen=True)
class SourceConfig:
    name: str
    label: str
    group: str
    kind: str
    url: str
    target_dir: str
    target_file: str
    summary: str
    filtered_file: str | None = None
    department_code: str | None = None
    delimiter: str = ","

    @property
    def target_path(self):
        return repo_path(self.target_dir) / self.target_file

    @property
    def filtered_path(self):
        if self.filtered_file is None:
            return None
        return repo_path(self.target_dir) / self.filtered_file


def _read_toml() -> dict[str, Any]:
    config_path = repo_path("config/sources.toml")
    with config_path.open("rb") as handle:
        return tomllib.load(handle)


def load_sources() -> dict[str, SourceConfig]:
    data = _read_toml()
    sources = data.get("sources", {})
    result: dict[str, SourceConfig] = {}

    for name, payload in sources.items():
        result[name] = SourceConfig(
            name=name,
            label=payload["label"],
            group=payload["group"],
            kind=payload["kind"],
            url=payload["url"],
            target_dir=payload["target_dir"],
            target_file=payload["target_file"],
            summary=payload["summary"],
            filtered_file=payload.get("filtered_file"),
            department_code=payload.get("department_code"),
            delimiter=payload.get("delimiter", ","),
        )

    return result

