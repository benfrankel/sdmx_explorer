import pandas as pd
import requests
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.theme import Theme
import sdmx
from sdmx.source import NoSource

import logging

logger = logging.getLogger(__name__)


class SdmxClient:
    def __init__(self):
        # SDMX context:
        self.client = sdmx.Client()
        self.dataflows = None
        self.selected_dataflow = None
        self.dimensions = None
        self.selected_dimension = None

        # Display:
        self.locale = "en"
        self.verbose = False
        self.max_unpaged_rows = 12
        theme = {
            "info": "italic dim",
            "error": "bold red",
            "commands": "italic purple",
            "prompt": "bold",
            "index": "bold purple",
            "source": "yellow",
            "dataflow": "green",
            "dimension": "cyan",
        }
        self.console = Console(theme=Theme(theme))

    def repl(self):
        self._welcome()
        while self.client is not None:
            self._show_commands()
            command = self._prompt()
            self._dispatch(command)
            self.console.print()

    # TODO: Maybe this should do the same thing as `self._help()`.
    def _welcome(self):
        pass

    def _show_commands(self):
        self.console.print(
            "(H)elp, (E)xit, (B)ack, (I)nfo, (L)ist, (#) Select",
            style="commands",
        )

    def _prompt(self):
        prefix = "[prompt]"
        if self.client.source is not NoSource:
            path = [f"[source]{escape(self.client.source.id)}[/]"]
            if self.selected_dataflow is not None:
                path.append(f"[dataflow]{escape(self.selected_dataflow.id)}[/]")
                if self.selected_dimension is not None:
                    path.append(f"[dimension]{escape(self.selected_dimension.id)}[/]")
            prefix += "/".join(path)

        prefix += "$[/] "

        try:
            return self.console.input(prefix)
        except EOFError:
            self.console.print()
            return "back"
        except KeyboardInterrupt:
            return "exit"

    def _dispatch(self, command):
        match _normalize(command):
            case "help" | "h" | "?" | "":
                self._help()
            case "verbose" | "v":
                self._toggle_verbose()
            case "clear" | "c":
                self._clear_cache()
            case "exit" | "end" | "e" | "quit" | "q":
                self._exit()
            case "back" | "b":
                self._back()
            case "info" | "i":
                self._info()
            case "list" | "ls" | "l":
                self._list()
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

    def _toggle_verbose(self):
        self.verbose = not self.verbose
        level = logging.INFO if self.verbose else logging.WARN
        logging.getLogger(__name__).setLevel(level)
        logging.getLogger("sdmx").setLevel(level)
        self.console.print(f"Verbose: [bold]{self.verbose}[/]", style="info")

    def _clear_cache(self):
        self.dataflows = None
        self.dimensions = None
        self.console.print("Cache cleared", style="info")

    def _exit(self):
        self.client = None

    def _back(self):
        if self.selected_dimension is not None:
            self.selected_dimension = None
        elif self.selected_dataflow is not None:
            self.selected_dataflow = None
            # TODO: Store this as a map so users won't have to redownload later if they return.
            self.dimensions = None
        elif self.client.source is not NoSource:
            self.client.source = NoSource
            self.dataflows = None
        else:
            self._exit()

    # TODO: Print info about the selected resource.
    def _info(self):
        pass

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
        for idx, id in enumerate(sdmx.list_sources()):
            source = sdmx.get_source(id)
            table.add_row(str(idx), id, source.name)
        self._print_table(table)

    def _list_dataflows(self):
        if not self._populate_dataflows():
            return

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
        for idx, dfd in enumerate(sorted(self.dataflows.values())):
            table.add_row(
                str(idx),
                dfd.id,
                self._localize(dfd.name),
                self._localize(dfd.description),
            )
        self._print_table(table)

    def _list_dimensions(self):
        if not self._populate_dimensions():
            return

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
        for idx, dim in enumerate(self.dimensions):
            concept = dim.concept_identity
            table.add_row(
                str(idx),
                dim.id,
                self._localize(concept.name),
                self._localize(concept.description),
            )
        self._print_table(table)

    def _list_codes(self):
        concept = self.selected_dimension.concept_identity
        codelist = concept.core_representation.enumerated
        codes = sorted(codelist.items.values())

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
            style="dimension",
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
        for idx, code in enumerate(codes):
            table.add_row(
                str(idx),
                code.id,
                self._localize(code.name),
                self._localize(code.description),
            )
        self._print_table(table)

    def _select(self, idx):
        if self.client.source is NoSource:
            self._select_source(idx)
        elif self.selected_dataflow is None:
            self._select_dataflow(idx)
        elif self.selected_dimension is None:
            self._select_dimension(idx)
        else:
            self._print_error("Nothing to select.")

    def _select_source(self, idx):
        sources = sdmx.list_sources()
        if not 0 <= idx < len(sources):
            self._print_error(f'Invalid source index "{idx}".')
            return
        self.client.source = sdmx.get_source(sources[idx])
        if self.verbose:
            self.console.print(
                f"Selected source: [source]{escape(self.client.source.id)}[/]",
                style="info",
            )

    def _select_dataflow(self, idx):
        if not self._populate_dataflows():
            return

        if not 0 <= idx < len(self.dataflows):
            self._print_error(f'Invalid dataflow index "{idx}".')
            return
        self.selected_dataflow = sorted(self.dataflows.values())[idx]
        if self.verbose:
            self.console.print(
                f"Selected dataflow: [dataflow]{escape(self.selected_dataflow.id)}[/]",
                style="info",
            )

    def _select_dimension(self, idx):
        if not self._populate_dimensions():
            return

        if not 0 <= idx < len(self.dimensions):
            self._print_error(f'Invalid dimension index "{idx}".')
            return
        self.selected_dimension = self.dimensions[idx]
        if self.verbose:
            self.console.print(
                f"Selected dimension: [dimension]{escape(self.selected_dimension.id)}[/]",
                style="info",
            )

    def _populate_dataflows(self):
        if not self.client.source.supports["dataflow"]:
            self._print_error(
                f"[source]{self.client.source.id}[/] does not support listing dataflows.",
            )
            return False

        if self.dataflows is None:
            try:
                with self.console.status("Requesting dataflows..."):
                    msg = self.client.dataflow()
            except KeyboardInterrupt:
                self.console.print("Request canceled", style="info")
                return False
            except requests.exceptions.ConnectionError as e:
                self._print_error(f"Connection error: {e}.")
                return False
            self.dataflows = msg.dataflow

        return True

    def _populate_dimensions(self):
        if not self.client.source.supports["datastructure"]:
            self._print_error(
                f"[source]{self.client.source.id}[/] does not support listing dimensions",
            )
            return False

        if self.dimensions is None:
            try:
                with self.console.status("Requesting dimensions..."):
                    msg = self.client.datastructure(
                        resource=self.selected_dataflow.structure,
                    )
            except KeyboardInterrupt:
                self.console.print("Request canceled", style="info")
                return False
            except requests.exceptions.ConnectionError as e:
                self._print_error(f"Connection error: {e}.")
                return False
            dsd = msg.structure[self.selected_dataflow.structure.id]
            self.dimensions = dsd.dimensions.components

        return True

    def _print_error(self, msg):
        self.console.print(f"[error]Error:[/] {msg}")

    def _print_table(self, table):
        if table.row_count <= self.max_unpaged_rows:
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
