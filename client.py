import pandas as pd
import requests
import requests_cache
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.theme import Theme
import sdmx
from sdmx.source import NoSource
from sdmx.model import TimeDimension

from datetime import timedelta
import logging
import readline
import traceback

logger = logging.getLogger(__name__)


class SdmxClient:
    def __init__(self):
        # SDMX context:
        self.client = sdmx.Client(backend="sqlite", expire_after=timedelta(days=1))
        self.selected_dataflow = None
        self.selected_dimension = None
        self.selected_codes = dict()

        # Display:
        self.locale = "en"
        self.verbose = False
        self.max_unpaged_rows = 12
        theme = {
            "help": "italic purple",
            "info": "italic dim",
            "error": "bold red",
            "index": "bold purple",
            "source": "yellow",
            "dataflow": "green",
            "dimension": "cyan",
            "code": "blue",
        }
        self.console = Console(theme=Theme(theme), highlight=False)

    def repl(self):
        self._welcome()
        while self.client is not None:
            try:
                self._show_commands()
                command = self._prompt()
                self._dispatch(command)
            except KeyboardInterrupt:
                self._print_info("Interrupted")
            except Exception as err:
                if self.verbose:
                    logger.exception("Exception raised:")
                else:
                    self._print_error(f"{err!r}")
            self.console.print()

    # TODO: Maybe this should do the same thing as `self._help()`.
    def _welcome(self):
        pass

    def _show_commands(self):
        self.console.print(
            "Commands: (H)elp, (E)xit, (B)ack, (S)how, (L)ist, (#) Select",
            style="help",
        )

    def _prompt(self):
        key = []
        try:
            dimensions = self._fetch_dimensions(quiet=True) or []
        except Exception:
            dimensions = []
        for dim in dimensions:
            dim_codes = self.selected_codes.setdefault(dim.id, set())
            if dim_codes:
                s = "+".join(
                    f"[b][code]{escape(code.id)}[/][/]" for code in sorted(dim_codes)
                )
            else:
                s = "*"
            if (
                self.selected_dimension is not None
                and self.selected_dimension.id == dim.id
            ):
                s = f"[u]{s}[/]"
            key.append(s)
        key = ".".join(key)
        if key:
            key = f"({key})"

        path = []
        if self.client.source is not NoSource:
            path = [f"[b][source]{escape(self.client.source.id)}[/][/]"]
        if self.selected_dataflow is not None:
            path.append(
                f"[b][dataflow]{escape(self.selected_dataflow.id)}[/][/]{key}",
            )
        if self.selected_dimension is not None:
            path.append(f"[b][dimension]{escape(self.selected_dimension.id)}[/][/]")
        path = "/".join(path)

        prefix = f"{path}> "
        try:
            return self.console.input(prefix)
        except EOFError:
            if self.client.source is not NoSource:
                self.console.print()
            return "back"
        except BaseException as err:
            self.console.print()
            raise err

    def _dispatch(self, command):
        match _normalize(command):
            case "":
                pass
            case "help" | "h" | "?":
                self._help()
            case "verbose" | "v":
                self._toggle_verbose()
            case "clear" | "c":
                self._clear_cache()
            case "exit" | "end" | "e" | "quit" | "q":
                self._exit()
            case "back" | "b":
                self._back()
            case "show" | "s":
                self._show()
            case "list" | "ls" | "l":
                self._list()
            case "data" | "d":
                self._data()
            case _:
                try:
                    idx = int(command)
                except ValueError:
                    self._print_error(f'Invalid command "{escape(command)}".')
                    return
                self._select(idx)

    # TODO: Explain how to use the REPL.
    def _help(self):
        pass

    def _toggle_verbose(self, quiet=False):
        self.verbose = not self.verbose
        level = logging.INFO if self.verbose else logging.WARN
        logger.setLevel(level)
        logging.getLogger("sdmx").setLevel(level)
        if not quiet:
            self._print_info(f"Verbose: [b]{self.verbose}[/]")

    def _clear_cache(self):
        self.client.clear_cache()
        requests_cache.clear()
        self._print_info("Cache cleared")

    def _exit(self):
        self.client = None

    def _back(self):
        if self.selected_dimension is not None:
            self.selected_dimension = None
        elif self.selected_dataflow is not None:
            self.selected_dataflow = None
            self.selected_codes = dict()
        elif self.client.source is not NoSource:
            self.client.source = NoSource
        else:
            self._exit()

    def _show(self):
        if self.client.source is NoSource:
            self._print_error("Nothing is selected.")
            return

        # Define table.
        table = Table(
            show_edge=False,
            show_lines=True,
        )
        table.add_column(
            overflow="fold",
            style="bold",
        )
        table.add_column(
            header="#",
            style="index",
            justify="right",
        )
        table.add_column(
            header="ID",
            overflow="fold",
        )
        table.add_column(
            header="Name",
            overflow="fold",
        )
        table.add_column(
            header="Description",
            overflow="fold",
        )

        # Populate table.
        sources = sdmx.list_sources()
        source_idx = sources.index(self.client.source.id)
        table.add_row(
            "Source",
            str(source_idx),
            f"[source]{escape(self.client.source.id)}[/]",
            escape(self.client.source.name),
            f"[dim][link {self.client.source.url}]{escape(self.client.source.url)}[/][/]",
        )
        if self.selected_dataflow is not None:
            dataflows = sorted(self._fetch_dataflows().values())
            dataflow_idx = dataflows.index(self.selected_dataflow)
            table.add_row(
                "Dataflow",
                str(dataflow_idx),
                f"[dataflow]{escape(self.selected_dataflow.id)}[/]",
                escape(self._localize(self.selected_dataflow.name)),
                escape(self._localize(self.selected_dataflow.description)),
            )
        if self.selected_dimension is not None:
            dimensions = self._fetch_dimensions()
            dimension_idx = dimensions.index(self.selected_dimension)
            concept = self.selected_dimension.concept_identity
            table.add_row(
                "Dimension",
                str(dimension_idx),
                f"[dimension]{escape(self.selected_dimension.id)}[/]",
                escape(self._localize(concept.name)),
                escape(self._localize(concept.description)),
            )
            dim_codes = self.selected_codes.setdefault(
                self.selected_dimension.id, set()
            )
            for code in sorted(dim_codes):
                codes = self._fetch_codes()
                code_idx = codes.index(code)
                table.add_row(
                    "Code",
                    str(code_idx),
                    f"[code]{escape(code.id)}[/]",
                    escape(self._localize(code.name)),
                    escape(self._localize(code.description)),
                )

        # Display table.
        self._print_table(table)

    def _list(self):
        if self.client.source is NoSource:
            self._list_sources()
        elif self.selected_dataflow is None:
            self._list_dataflows()
        elif self.selected_dimension is None:
            self._list_dimensions()
        else:
            self._list_codes()

    def _list_sources(self):
        # Define table.
        table = Table(
            show_edge=False,
            show_lines=True,
        )
        table.add_column(
            header="#",
            style="index",
            justify="right",
        )
        table.add_column(
            header="Source ID",
            style="source",
            overflow="fold",
        )
        table.add_column(
            header="Source Name",
            overflow="fold",
        )
        table.add_column(
            header="Source URL",
            overflow="fold",
            style="dim",
        )

        # Populate table.
        for idx, source_id in enumerate(sdmx.list_sources()):
            source = sdmx.get_source(source_id)
            table.add_row(
                str(idx),
                escape(source_id),
                escape(source.name),
                f"[link {source.url}]{escape(source.url)}[/]",
            )

        # Display table.
        self._print_table(table)

    def _list_dataflows(self):
        dataflows = self._fetch_dataflows()
        if dataflows is None:
            return

        # Define table.
        table = Table(
            show_edge=False,
            show_lines=True,
        )
        table.add_column(
            header="#",
            style="index",
            justify="right",
        )
        table.add_column(
            header="Dataflow ID",
            style="dataflow",
            overflow="fold",
        )
        table.add_column(
            header="Dataflow Name",
            overflow="fold",
        )
        table.add_column(
            header="Dataflow Description",
            overflow="fold",
        )

        # Populate table.
        for idx, dfd in enumerate(sorted(dataflows.values())):
            table.add_row(
                str(idx),
                escape(dfd.id),
                escape(self._localize(dfd.name)),
                escape(self._localize(dfd.description)),
            )

        # Display table.
        self._print_table(table)

    def _list_dimensions(self):
        dimensions = self._fetch_dimensions()
        if dimensions is None:
            return

        # Define table.
        table = Table(
            show_edge=False,
            show_lines=True,
        )
        table.add_column(
            header="#",
            style="index",
            justify="right",
        )
        table.add_column(
            header="Dimension ID",
            style="dimension",
            overflow="fold",
        )
        table.add_column(
            header="Concept Name",
            overflow="fold",
        )
        table.add_column(
            header="Concept Description",
            overflow="fold",
        )

        # Populate table.
        for idx, dim in enumerate(dimensions):
            concept = dim.concept_identity
            table.add_row(
                str(idx),
                escape(dim.id),
                escape(self._localize(concept.name)),
                escape(self._localize(concept.description)),
            )

        # Display table.
        self._print_table(table)

    def _list_codes(self):
        codes = self._fetch_codes()
        if codes is None:
            return

        # Define table.
        table = Table(
            show_edge=False,
            show_lines=True,
        )
        table.add_column(
            header="#",
            style="index",
            justify="right",
        )
        table.add_column(
            header="Code ID",
            style="code",
            overflow="fold",
        )
        table.add_column(
            header="Code Name",
            overflow="fold",
        )
        table.add_column(
            header="Code Description",
            overflow="fold",
        )

        # Populate table.
        for idx, code in enumerate(codes):
            table.add_row(
                str(idx),
                escape(code.id),
                escape(self._localize(code.name)),
                escape(self._localize(code.description)),
            )

        # Display table.
        self._print_table(table)

    def _select(self, idx):
        if self.client.source is NoSource:
            self._select_source(idx)
        elif self.selected_dataflow is None:
            self._select_dataflow(idx)
        elif self.selected_dimension is None:
            self._select_dimension(idx)
        else:
            self._select_code(idx)

    def _select_source(self, idx):
        sources = sdmx.list_sources()

        if not 0 <= idx < len(sources):
            self._print_error(f'Invalid source index "{idx}".')
            return
        self.client.source = sdmx.get_source(sources[idx])

        self._print_info(f"Selected source: [source]{escape(self.client.source.id)}[/]")

    def _select_dataflow(self, idx):
        dataflows = self._fetch_dataflows()
        if dataflows is None:
            return

        if not 0 <= idx < len(dataflows):
            self._print_error(f'Invalid dataflow index "{idx}".')
            return
        self.selected_dataflow = sorted(dataflows.values())[idx]

        # Pre-fetch dimensions so that `self._prompt` can get the number of dimensions.
        self._fetch_dimensions()

        self._print_info(
            f"Selected dataflow: [dataflow]{escape(self.selected_dataflow.id)}[/]"
        )

    def _select_dimension(self, idx):
        dimensions = self._fetch_dimensions()
        if dimensions is None:
            return

        if not 0 <= idx < len(dimensions):
            self._print_error(f'Invalid dimension index "{idx}".')
            return
        self.selected_dimension = dimensions[idx]

        self._print_info(
            f"Selected dimension: [dimension]{escape(self.selected_dimension.id)}[/]"
        )

    def _select_code(self, idx):
        codes = self._fetch_codes()
        if codes is None:
            return

        if not 0 <= idx < len(codes):
            self._print_error(f'Invalid code index "{idx}".')
            return
        code = codes[idx]
        dim_codes = self.selected_codes.setdefault(self.selected_dimension.id, set())
        dim_codes.symmetric_difference_update(code)

        self._print_info(
            f"[dimension]{self.selected_dimension.id}[/]: {["Removed", "Added"][code in dim_codes]} [code]{code}[/]"
        )

    def _data(self, quiet=False):
        if self.selected_dataflow is None:
            if not quiet:
                self._print_error("No dataflow selected.")
            return

        key = []
        for dim in self._fetch_dimensions() or []:
            dim_codes = self.selected_codes.setdefault(dim.id, set())
            if dim_codes:
                key.append("+".join(code.id for code in sorted(dim_codes)))
            else:
                key.append("*")
        key = ".".join(key)

        msg = self._get(
            "data",
            resource_type="data",
            resource_id=self.selected_dataflow.id,
            key=key,
        )
        if msg is None:
            return

        self.console.print(msg)

    def _fetch_dataflows(self, quiet=False):
        if not self.client.source.supports["dataflow"]:
            if not quiet:
                self._print_error(
                    f"[source]{self.client.source.id}[/] does not support listing dataflows."
                )
            return

        msg = self._get(
            "dataflows",
            resource_type="dataflow",
        )
        if msg is None:
            return

        return msg.dataflow

    def _fetch_dimensions(self, quiet=False):
        if not self.client.source.supports["datastructure"]:
            if not quiet:
                self._print_error(
                    f"[source]{self.client.source.id}[/] does not support listing dimensions."
                )
            return
        if self.selected_dataflow is None:
            return

        dsd = self.selected_dataflow.structure
        msg = self._get(
            "dimensions",
            resource_type="datastructure",
            resource_id=dsd.id,
            agency_id=dsd.maintainer.id,
            params={"references": "children"},
        )
        if msg is None:
            return

        dsd = msg.structure[dsd.id]
        return [dim for dim in dsd.dimensions.components if type(dim) != TimeDimension]

    def _fetch_codes(self, quiet=False):
        if not self.client.source.supports["codelist"]:
            if not quiet:
                self._print_error(
                    f"[source]{self.client.source.id}[/] does not support listing codes."
                )
            return
        if self.selected_dimension is None:
            return

        dim = self.selected_dimension
        rep = dim.local_representation or dim.concept_identity.core_representation
        codelist = rep.enumerated
        if codelist is None:
            if not quiet:
                self._print_error(f"No codelist for [dimension]{dim.id}[/] dimension.")
            return

        msg = self._get(
            "codes",
            resource_type="codelist",
            resource_id=codelist.id,
            agency_id=codelist.maintainer.id,
        )
        if msg is None:
            return

        return sorted(msg.codelist[codelist.id].items.values())

    def _get(self, target, **kwargs):
        # TODO: Open an issue for `dry_run=True` still logging. This is a workaround to get the URL without logging.
        if self.verbose:
            self._toggle_verbose(quiet=True)
            req = self.client.get(dry_run=True, **kwargs)
            self._toggle_verbose(quiet=True)
        else:
            req = self.client.get(dry_run=True, **kwargs)
        if req.url in self.client.cache:
            return self.client.cache[req.url]

        with self.console.status(
            f"Fetching {target}: [dim][link {req.url}]{escape(req.url)}[/][/]"
        ):
            msg = self.client.get(use_cache=True, **kwargs)

        # TODO: Workaround for <https://github.com/khaeru/sdmx/issues/256>.
        self.client.cache[req.url] = msg
        return msg

    def _print_info(self, msg):
        self.console.print(msg, style="info", highlight=True)

    def _print_error(self, msg):
        self.console.print(f"[error]Error:[/] {msg}", highlight=True)

    def _print_table(self, table):
        if table.row_count == 0:
            self.console.print("No results.", style="info")
        elif table.row_count <= self.max_unpaged_rows:
            self.console.print(table)
        else:
            with self.console.pager(styles=True, links=True):
                self.console.print(table)

    def _localize(self, s):
        return s.localized_default(self.locale)


def _normalize(s):
    return s.lower()


if __name__ == "__main__":
    SdmxClient().repl()
