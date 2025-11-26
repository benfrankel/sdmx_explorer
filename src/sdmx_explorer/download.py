import numpy as np
import pandas as pd
import sdmx

from pathlib import Path

from . import auth
from .context import SdmxContext
from .display import CONSOLE
from .query import load_paths


CACHE_DIR: Path = Path(__file__).parent.parent.parent / "cache"
DEFAULT_DOWNLOAD_PATH: Path = Path("download.tsv")


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

    download = []
    for query in load_paths():
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
        # Cache the query result.
        save_as(df, cache_path(query))
        console.print(f"Downloaded {len(df)} rows for {query_str}", highlight=True)

        df.insert(0, "SOURCE_ID", query.source)
        df.insert(1, "DATAFLOW_ID", query.dataflow)
        download.append(df)

    # Save the entire download in a single file.
    if download:
        df = pd.concat(download, ignore_index=True).drop_duplicates()
        df = pivot(df)
        columns = ["SOURCE_ID", "DATAFLOW_ID"] + [
            x for x in df.columns.tolist() if x != "SOURCE_ID" and x != "DATAFLOW_ID"
        ]
        df = df[columns]
        save_as(df, DEFAULT_DOWNLOAD_PATH)


def pivot(df):
    """Pivot a table so that each row represents an entire time series."""
    TIME = "TIME_PERIOD"
    VALUE = "value"
    NAN_MARKER = "__THIS_IS_NAN__"
    return (
        df.fillna(NAN_MARKER)
        .pivot_table(
            index=set(df.columns.tolist()).difference([TIME, VALUE]),
            columns=TIME,
            values=VALUE,
        )
        .reset_index()
        .replace(NAN_MARKER, np.nan)
    )


def save_as(df, path):
    """Save a table to a given file path with an inferred format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    match path.suffix:
        case ".csv":
            df.to_csv(path, index=False)
        case ".xlsx" | ".xls":
            df.to_excel(path, index=False)
        case ".html":
            df.to_html(path, index=False)
        case ".json":
            df.to_json(path, index=False)
        case ".parquet":
            df.to_parquet(path, index=False)
        case ".feather":
            df.to_feather(path, index=False)
        case ".pkl" | ".pickle":
            df.to_pickle(path, index=False)
        case ".tex":
            df.to_latex(path, index=False)
        case ".dta":
            df.to_stata(path, index=False)
        case _:
            df.to_csv(path, sep="\t", index=False)


def cache_path(query):
    return CACHE_DIR / query.source / query.dataflow / f"{query.key}.tsv"
