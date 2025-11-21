from .init import init

init()

import rich
from rich.console import Console
import sdmx

import traceback

from .display import CONSOLE
from .query import load_queries


def main():
    console = CONSOLE
    client = sdmx.Client()
    for query in load_queries():
        with console.status(f"Fetching {query.to_str(rich=True)}"):
            try:
                msg = query.download(client)
            except Exception:
                console.print_exception(show_locals=True)
                continue

        if msg is None:
            console.print(
                f"[error]Error:[/] No matching time series for {query.to_str(rich=True)}"
            )
            continue

        rows = len(next(iter(msg.data[0].series.values())))
        console.print(
            f"Downloaded {rows} rows for {query.to_str(rich=True)}",
            highlight=True,
        )


if __name__ == "__main__":
    main()
