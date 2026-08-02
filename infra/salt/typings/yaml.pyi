from typing import TypeAlias

YamlValue: TypeAlias = (
    dict[str, "YamlValue"] | list["YamlValue"] | str | int | float | bool | None
)

def safe_load(stream: str) -> YamlValue: ...
