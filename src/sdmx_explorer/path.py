from rich.markup import escape

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SdmxPath:
    """A partial SDMX path to a particular view of statistical data."""

    source: str | None
    dataflow: str | None
    key: str | None

    @classmethod
    def from_str(cls, s):
        source, dataflow, key, *_ = s.split(sep="/", maxsplit=2) + [None] * 3
        if key and "/" in key:
            raise ValueError(f"Failed to parse {s!r} as an SDMX path: Too many parts")
        return cls(source=source, dataflow=dataflow, key=key)

    def __post_init__(self):
        if (self.key and not self.dataflow) or (self.dataflow and not self.source):
            raise ValueError(
                f"Invalid SDMX path: {self.source!r}/{self.dataflow!r}/{self.key!r}"
            )

    def __str__(self):
        return self.to_str()

    def to_str(self, rich=False, dimensions=None):
        parts = []
        if self.source is not None:
            parts.append(f"[source]{escape(self.source)}[/]" if rich else self.source)
            if self.dataflow is not None:
                parts.append(
                    f"[dataflow]{escape(self.dataflow)}[/]" if rich else self.dataflow
                )
                if self.key is not None:
                    key_parts = []
                    for i, key_part in enumerate(self.key.split(".")):
                        if rich:
                            key_part = "+".join(
                                code if code == "*" else f"[code]{escape(code)}[/]"
                                for code in key_part.split("+")
                            )
                        if dimensions is not None and i in dimensions:
                            key_part = (
                                f"[u][dimension]{escape(dimensions[i])}[/]={key_part}[/]"
                                if rich
                                else f"{dimensions[i]}={key_part}"
                            )
                        key_parts.append(key_part)
                    key = ".".join(key_parts)
                    parts.append(key)
        return "/".join(parts)


@dataclass(frozen=True)
class SdmxQuery(SdmxPath):
    """A full SDMX path to a particular view of statistical data."""

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.source, str):
            raise TypeError(f"Source must be a string: {self.source!r}")
        if not isinstance(self.dataflow, str):
            raise TypeError(f"Dataflow must be a string: {self.dataflow!r}")
        if not isinstance(self.key, str):
            raise TypeError(f"Key must be a string: {self.key!r}")


BOOKMARKS_PATH: Path = Path(__file__).parent.parent.parent / "bookmarks.txt"


def load_bookmarks() -> list[SdmxPath]:
    try:
        with open(BOOKMARKS_PATH, "r") as f:
            return [
                SdmxPath.from_str(line.strip())
                for line in f
                if line and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []


def save_bookmark(path: SdmxPath):
    if path in load_bookmarks():
        raise ValueError(f"Path already bookmarked: {path}")

    with open(BOOKMARKS_PATH, "a") as f:
        f.write(f"{path}\n")
