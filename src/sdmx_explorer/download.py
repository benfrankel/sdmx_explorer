import numpy as np
import pandas as pd
import sdmx

from pathlib import Path

from . import auth
from .context import SdmxContext
from .display import CONSOLE
from .query import load_queries


DOWNLOAD_PATH: Path = Path("data")


def main():
    try:
        download()
    except KeyboardInterrupt:
        print("Interrupted")


def download():
    console = CONSOLE
    ctx = SdmxContext(client=auth.client(), console=console)

    # TODO: Actually fix the warning instead of suppressing it.
    sdmx.log.setLevel(100)

    dfs = []
    for query in load_queries():
        query_str = query.to_str(rich=True)
        with console.status(f"Downloading {query_str}"):
            try:
                ctx.select_query(query)
                df: pd.DataFrame = ctx.data()
            except Exception:
                # TODO: Put this behind a verbose flag.
                console.print_exception(show_locals=True)
                continue

        if df is None:
            console.print(f"[warning]Warning:[/] No results for {query_str}")
            continue

        # TODO: Make this optional.
        # Prune unimportant columns to reduce file size.
        to_drop = set(df.columns.tolist())
        to_drop.difference_update(x.id for x in ctx.dimensions())
        to_drop.remove("value")
        to_drop.add("FREQUENCY")
        df = df.drop(columns=to_drop)

        # TODO: Make this optional.
        dfs.append(df)

        # TODO: Make this optional.
        # Pivot data so each row represents an entire time series.
        df = pivot(df)

        # Save each download in its own file.
        save_download(query, df)
        console.print(f"Downloaded {len(df)} rows for {query_str}", highlight=True)

    # Save all downloads together in a single file.
    if dfs:
        # TODO: Add columns for source and dataflow IDs.
        full = pd.concat(dfs, ignore_index=True).drop_duplicates()
        full = pivot(full)
        save_full(full)


def pivot(df):
    NAN_MARKER = "__THIS_IS_NAN__"
    df = df.fillna(NAN_MARKER)
    df = df.pivot_table(
        index=set(df.columns.tolist()).difference(["TIME_PERIOD", "value"]),
        columns="TIME_PERIOD",
        values="value",
    ).reset_index()
    df = df.replace(NAN_MARKER, np.nan)
    return df


def save_download(query, df):
    path = download_path(query)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)


def save_full(df):
    path = DOWNLOAD_PATH / "full.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)


def download_path(query):
    return DOWNLOAD_PATH / query.source / query.dataflow / f"{query.key}.tsv"
