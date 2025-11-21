from .init import init

init()

import pandas as pd
import sdmx

from .display import CONSOLE
from .query import load_queries, DATA_PATH


def main():
    console = CONSOLE
    client = sdmx.Client()

    dfs = []
    for query in load_queries():
        query_str = query.to_str(rich=True)
        with console.status(f"Fetching {query_str}"):
            try:
                df = query.download(client=client)
            except Exception:
                console.print_exception(show_locals=True)
                continue

        if df is None:
            console.print(f"[error]Error:[/] No matching time series for {query_str}")
            continue

        dfs.append(df)
        console.print(f"Downloaded {len(df)} rows for {query_str}", highlight=True)

    if dfs:
        full = pd.concat(dfs).drop_duplicates()
        path = DATA_PATH / "full.tsv"
        path.parent.mkdir(parents=True, exist_ok=True)
        full.to_csv(path, sep="\t", index=False)


if __name__ == "__main__":
    main()
