from rich.markup import escape

from pathlib import Path
from typing import NamedTuple


QUERIES_PATH: Path = Path("queries.txt")


class Query(NamedTuple):
    source: str
    dataflow: str
    key: str

    @classmethod
    def from_str(cls, s):
        try:
            source, dataflow, key = s.split(sep="/")
        except ValueError:
            raise ValueError(f'Failed to parse string "{s}" as a query')
        return cls(source=source, dataflow=dataflow, key=key)

    def __str__(self):
        return self.to_str()

    def to_str(self, rich=False):
        if rich:
            key = ".".join(
                "+".join(
                    code if code == "*" else f"[code]{escape(code)}[/]"
                    for code in dimension.split("+")
                )
                for dimension in self.key.split(".")
            )
            return f"[source]{escape(self.source)}[/]/[dataflow]{escape(self.dataflow)}[/]/{key}"
        else:
            return "/".join(self)


def load_queries():
    try:
        with open(QUERIES_PATH, "r") as f:
            return [
                Query.from_str(line.strip())
                for line in f
                if line and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []


def save_query(query):
    if query in load_queries():
        raise ValueError(f"Query already saved: {query}")

    with open(QUERIES_PATH, "a") as f:
        f.write(f"{query}\n")
