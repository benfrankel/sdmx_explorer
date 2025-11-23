from .init import init

init()

import pandas as pd

from . import auth
from .display import CONSOLE
from .query import load_queries, DATA_PATH


def main():
    try:
        download()
    except KeyboardInterrupt:
        print("Interrupted")


def download():
    console = CONSOLE
    client = auth.client()

    # TODO: Actually fix the warning.
    # sdmx.log.setLevel(100)

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
            console.print(f"[warning]Warning:[/] No results for {query_str}")
            continue

        dfs.append(df)
        console.print(f"Downloaded {len(df)} rows for {query_str}", highlight=True)

    # TODO: Remove the exit().
    exit()
    if dfs:
        full = pd.concat(dfs, ignore_index=True).drop_duplicates()
        path = DATA_PATH / "full.tsv"
        path.parent.mkdir(parents=True, exist_ok=True)
        full.to_csv(path, sep="\t", index=False)
