from rich.markup import escape
import sdmx

from pathlib import Path
from typing import NamedTuple

from . import auth


QUERIES_PATH: Path = Path("queries.txt")
DATA_PATH: Path = Path("data")


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
            key = []
            for dim_codes in self.key.split("."):
                options = []
                for option in dim_codes.split(";"):
                    codes = []
                    for code in option.split("+"):
                        if code == "*":
                            codes.append(code)
                        else:
                            codes.append(f"[code]{escape(code)}[/]")
                    options.append("+".join(codes))
                key.append(";".join(options))
            key = ".".join(key)

            return f"[source]{escape(self.source)}[/]/[dataflow]{escape(self.dataflow)}[/]/{key}"
        else:
            return "/".join(self)

    def download(self, client=None):
        df = self.data(client=client)
        if df is not None:
            self.save_data(df)
        return df

    def data(self, client=None):
        if client is None:
            client = auth.client()

        try:
            client.source = sdmx.get_source(self.source)
        except KeyError:
            raise ValueError(f'Source with ID "{self.source}" was not found')

        msg = client.get(
            resource_type="data",
            resource_id=self.dataflow,
            key=self.key,
        )

        if msg.data[0].series:
            return sdmx.to_pandas(msg).reset_index()

    def save_data(self, df):
        path = self._data_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, sep="\t", index=False)

    def _data_path(self):
        return DATA_PATH / self.source / self.dataflow / f"{self.key}.tsv"


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
