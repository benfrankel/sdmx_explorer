import numpy as np
import pandas as pd
from rich.markup import escape
import sdmx
import yaml

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import tomllib

from . import auth
from .context import SdmxContext
from .display import CONSOLE
from .path import SdmxQuery


def main():
    try:
        return _main()
    except KeyboardInterrupt:
        print("Interrupted")
        return 130


def _main():
    console = CONSOLE

    parser = argparse.ArgumentParser(
        add_help=False,
        usage="download [-v|--verbose] <DOWNLOAD_CONFIG_PATH>...",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Output additional information for debugging purposes.",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this message.",
    )
    parser.add_argument(
        dest="paths",
        metavar="DOWNLOAD_CONFIG_PATH",
        type=Path,
        nargs="+",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    # TODO: Actually fix the warning instead of suppressing it.
    if not args.verbose:
        sdmx.log.setLevel(100)

    for path in duplicates(args.paths):
        console.print(
            f"[warning]Warning:[/] Download configuration file {escape(repr(str(path)))} appears multiple times",
            highlight=True,
        )

    try:
        ctx = SdmxContext(client=auth.client(), console=console)
        configs = [(path, DownloadConfig.load(path)) for path in args.paths]

        seen = set()
        for path, config in configs:
            if path in seen:
                continue
            seen.add(path)
            for query in duplicates(config.queries):
                console.print(
                    f"[warning]Warning:[/] Download configuration file {escape(repr(str(path)))} query appears multiple times: {query.to_str(rich=True)}",
                    highlight=True,
                )

        console.rule()
        for path, config in configs:
            console.print(
                f"[b]Starting download:[/] {escape(repr(str(path)))} -> {escape(repr(str(config.output_path)))}",
                highlight=True,
            )
            config.download(ctx=ctx, verbose=args.verbose)
            console.rule()
    except Exception as err:
        if args.verbose:
            console.print_exception(show_locals=True)
        else:
            console.print(f"[error]Error:[/] {escape(str(err))}", highlight=True)
        return getattr(err, "errno", 1)


@dataclass(frozen=True)
class DownloadConfig:
    output_path: Path
    queries: list[SdmxQuery]
    drop_columns: list[str] = field(default_factory=list)
    drop_attributes: bool = False
    pivot_table: bool = False
    use_cache: bool = True

    REQUIRED_FIELDS = ["output_path", "queries"]
    EXPECTED_FIELDS = {
        "output_path": str,
        "queries": list,
        "drop_columns": list,
        "drop_attributes": bool,
        "pivot_table": bool,
        "use_cache": bool,
    }
    SUPPORTED_TABLE_EXTENSIONS = {
        ".tsv",
        ".csv",
        ".xlsx",
        ".xls",
        ".html",
        ".json",
        ".parquet",
        ".feather",
        ".pkl",
        ".pickle",
        ".tex",
        ".dta",
    }

    @classmethod
    def load(cls, path: Path) -> "DownloadConfig":
        match path.suffix:
            case ".toml":
                with open(path) as f:
                    data = tomllib.load(f)
            case ".yaml":
                with open(path) as f:
                    data = yaml.safe_load(f)
            case _:
                raise ValueError(
                    f"Download configuration file {str(path)!r} uses an unsupported file extension: {path.suffix!r} (should be '.toml' or '.yaml')"
                )

        for key in cls.REQUIRED_FIELDS:
            if key not in data:
                raise TypeError(
                    f"Download configuration file {str(path)!r} is missing a required field: {key!r}"
                )
        for key, value in data.items():
            if key not in cls.EXPECTED_FIELDS:
                raise TypeError(
                    f"Download configuration file {str(path)!r} has an unexpected field: {key!r}"
                )
            expected_type = cls.EXPECTED_FIELDS[key]
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Download configuration file {str(path)!r} field {key!r} has the wrong type: {type(value).__name__!r} (should be {expected_type.__name__!r})"
                )

        data["output_path"] = path.parent / data["output_path"]
        if data["output_path"].suffix not in cls.SUPPORTED_TABLE_EXTENSIONS:
            raise TypeError(
                f"Download configuration file {str(path)!r} output path {str(data['output_path'])!r} has an unsupported file extension for tabular data: {data['output_path'].suffix!r}"
            )
        if data["output_path"].is_dir():
            raise IsADirectoryError(
                f"Download configuration file {str(path)!r} output path {str(data['output_path'])!r} already exists as a directory"
            )
        queries = []
        for query in data["queries"]:
            try:
                queries.append(SdmxQuery.from_str(query))
            except ValueError as err:
                raise ValueError(
                    f"Download configuration file {str(path)!r} query {query!r} is invalid: {err}"
                )
        data["queries"] = queries

        return cls(**data)

    def download(self, ctx=None, verbose=False):
        if ctx is None:
            ctx = SdmxContext(client=auth.client(), console=CONSOLE)

        download = []
        for query in self.queries:
            try:
                query_str = query.to_str(rich=True)
                with ctx.console.status(f"{query_str}"):
                    try:
                        ctx.select_source(query.source)
                    except KeyError:
                        ctx.console.print(
                            f"[error]Error:[/] No source found with ID {escape(repr(query.source))} in {query_str}",
                            highlight=True,
                        )
                        continue

                    try:
                        ctx.select_dataflow(query.dataflow)
                    except KeyError:
                        ctx.console.print(
                            f"[error]Error:[/] No dataflow found with ID {escape(repr(query.dataflow))} in {query_str}",
                            highlight=True,
                        )
                        continue

                    try:
                        ctx.select_key(query.key)
                    except KeyError as err:
                        ctx.console.print(
                            f"[error]Error:[/] No code found with ID {escape(str(err))} in {query_str}",
                            highlight=True,
                        )
                        continue
                    except ValueError as err:
                        ctx.console.print(
                            f"[error]Error:[/] {escape(str(err))} in {query_str}",
                            highlight=True,
                        )
                        continue

                    df: pd.DataFrame = ctx.data()

                if df is None:
                    ctx.console.print(
                        f"[warning]Warning:[/] No results for {query_str}"
                    )
                    continue

                # Drop empty observations.
                df = df.dropna(subset="value")

                # Cache the query result.
                if self.use_cache:
                    save_as(df, cache_path(query))

                ctx.console.print(
                    f"Received {len(df)} rows from {query_str}", highlight=True
                )

                # Drop attribute columns.
                if self.drop_attributes:
                    dimensions = set(x.id for x in ctx.dimensions())
                    measures = {"value"}
                    attributes = set(df.columns) - dimensions - measures
                    df = df.drop(columns=attributes)

                # Add columns for the SDMX source and dataflow.
                df.insert(0, "SOURCE_ID", query.source)
                df.insert(1, "DATAFLOW_ID", query.dataflow)

                # Add query result to download.
                download.append(df)
            except Exception as err:
                if verbose:
                    ctx.console.print_exception(show_locals=True)
                else:
                    ctx.console.print(
                        f"[error]Error:[/] {escape(repr(err))} while requesting {query_str}",
                        highlight=True,
                    )

        # Save the combined download to the output path.
        if download:
            df = pd.concat(download, ignore_index=True).drop_duplicates()

            # Pivot table so each row is an entire time series.
            if self.pivot_table:
                df = pivot(df)

            # Rearrange so that source and dataflow are the first two columns.
            PREFIX_COLS = ["SOURCE_ID", "DATAFLOW_ID"]
            other_cols = [x for x in df.columns if x not in PREFIX_COLS]
            df = df[PREFIX_COLS + other_cols]

            # Drop unwanted columns.
            for column in self.drop_columns:
                if column not in df.columns:
                    ctx.console.print(
                        f"[warning]Warning:[/] Cannot drop column {escape(repr(column))} that is already missing",
                        highlight=True,
                    )
            df = df.drop(columns=self.drop_columns, errors="ignore")

            # Save to output path.
            save_as(df, self.output_path)
            ctx.console.print(
                f"[b]Finished download:[/] Saved {len(df)} rows to {escape(repr(str(self.output_path)))}",
                highlight=True,
            )
        else:
            ctx.console.print(
                f"[warning]Warning:[/] Nothing to save to {escape(repr(str(self.output_path)))}",
                highlight=True,
            )


def pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot a table so that each row represents an entire time series."""
    TIME = "TIME_PERIOD"
    VALUE = "value"
    NAN_MARKER = "__THIS_IS_NAN__"
    return (
        df.fillna(NAN_MARKER)
        .pivot_table(
            index=set(df.columns).difference([TIME, VALUE]),
            columns=TIME,
            values=VALUE,
            # aggfunc='mean',
        )
        .reset_index()
        .replace(NAN_MARKER, np.nan)
    )


def save_as(df: pd.DataFrame, path: Path):
    """Save a table to a given file path with an inferred format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    match path.suffix:
        case ".tsv":
            df.to_csv(path, sep="\t", index=False)
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
            raise ValueError(
                f"Unsupported file extension for tabular data: {str(path)!r}"
            )


def cache_path(query: SdmxQuery) -> Path:
    """Get the file path where an SDMX query should be cached."""
    CACHE_DIR: Path = Path(__file__).parent.parent.parent / "cache"
    return CACHE_DIR / query.source / query.dataflow / f"{query.key}.tsv"


def duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen and item not in duplicates:
            duplicates.add(item)
            yield item
        seen.add(item)
