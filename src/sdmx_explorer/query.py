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

    def download(self, client=None):
        df = self.data(client=client)
        if df is not None:
            self.save_data(df)
        return df


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
    queries = load_queries()
    if query in queries:
        raise ValueError(f"Query already saved: {query}")
    queries.append(query)
    queries.sort()

    with open(QUERIES_PATH, "w") as f:
        f.writelines(f"{query}\n" for query in queries)
