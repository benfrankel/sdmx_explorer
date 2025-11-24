import requests_cache
from rich.markup import escape
from rich.table import Table
import sdmx
from sdmx.source import NoSource

import logging

from .context import SdmxContext
from .display import CONSOLE
from .query import save_query


log = logging.getLogger(__name__)


class SdmxRepl:
    def __init__(self, client=None):
        # Display:
        self.console = CONSOLE
        self.max_unpaged_rows = 12
        self.locale = "en"
        self.verbose = False

        # SDMX:
        self.ctx = SdmxContext(client, self.console)
        self.dimension = None

    def run(self):
        self.console.print("SDMX Explorer", style="bold purple")
        while self.ctx is not None:
            try:
                self._suggest_commands()
                command = self.prompt()
                self.run_command(command)
            except KeyboardInterrupt:
                self.console.print("Interrupted")
            except Exception as err:
                if self.verbose:
                    self.console.print_exception(show_locals=True)
                else:
                    self._print_error(f"{err!r}")
            self.console.print()

    def prompt(self):
        path = self.ctx.path(rich=True, selected_dimension=self.dimension)
        prefix = f"{path}> "

        try:
            return self.console.input(prefix).strip()
        except EOFError:
            if self.ctx.client.source is not NoSource:
                self.console.print()
            return "back"
        except BaseException as err:
            self.console.print()
            raise err

    def run_command(self, command):
        match command:
            case "":
                pass
            case "help" | "h" | "?":
                self.do_help()
            case "verbose" | "v":
                self.do_verbose()
            case "clear" | "c":
                self.do_clear()
            case "quit" | "q" | "exit" | "end" | "stop":
                self.do_quit()
            case "back" | "b":
                self.do_back()
            case "list" | "ls" | "l":
                self.do_list()
            case "info" | "i":
                self.do_info()
            # TODO: Add this command when SDMX 3.0 is better-supported.
            # case "preview" | "p":
            #     self.do_preview()
            case "save" | "s":
                self.do_save()
            case _:
                self.do_select(command)

    def do_help(self):
        child, children = self._child_resource_str()

        # Define table.
        table = Table(
            show_edge=True,
            show_lines=False,
        )
        table.add_column(
            header="Command",
            style="help",
            justify="right",
            overflow="fold",
        )
        table.add_column(
            header="Description",
            overflow="fold",
        )

        # Populate table.
        table.add_row(
            "help, h",
            "Show this help message [dim](aliases: ?)[/]",
        )
        table.add_row(
            "verbose, v",
            "Toggle verbose output",
        )
        table.add_row(
            "clear, c",
            "Clear the cache",
        )
        table.add_row(
            "quit, q",
            "Quit the session [dim](aliases: exit, end, stop)[/]",
        )
        table.add_row(
            "back, b",
            "Navigate back",
        )
        table.add_row(
            "list, l",
            f"List {children} [dim](aliases: ls)[/]",
        )
        table.add_row(
            "info, i",
            "Show information on the current selection",
        )
        # table.add_row(
        #    "preview, p",
        #    "Preview data from the current query",
        # )
        table.add_row(
            "save, s",
            "Save the current query",
        )
        table.add_row(
            "<INDEX>, <ID>",
            f"Select a {child}",
        )

        # Display table.
        self._print_table(table)

    def do_verbose(self, quiet=False):
        self.verbose = not self.verbose
        level = logging.INFO if self.verbose else logging.WARN
        log.setLevel(level)
        sdmx.log.setLevel(level)
        if not quiet:
            self.console.print(f"Verbose: [bold]{self.verbose}[/]", highlight=True)

    def do_clear(self):
        self.ctx.client.clear_cache()
        requests_cache.clear()
        self.console.print("Cache cleared")

    def do_quit(self):
        self.ctx = None

    def do_back(self):
        if self.dimension is not None:
            self.dimension = None
        elif not self.ctx.back():
            self.do_quit()

    def do_info(self):
        if self.ctx.client.source is NoSource:
            self._print_error("Nothing is selected.")
            return

        # Define table.
        table = Table(
            show_edge=True,
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
            header="Description / URL",
            overflow="fold",
        )

        # Populate table.
        if self.ctx.dataflow is not None:
            url = self.ctx.url()
            path = self.ctx.path(rich=True)
            table.add_row(
                "Query",
                "",
                path,
                "Selection",
                f"[dim][link {url}]{escape(url)}[/][/]",
            )

        source = self.ctx.client.source
        sources = sdmx.list_sources()
        source_idx = sources.index(source.id)
        table.add_row(
            "Source",
            str(source_idx),
            f"[source]{escape(source.id)}[/]",
            escape(source.name),
            f"[dim][link {source.url}]{escape(source.url)}[/][/]",
        )

        if self.ctx.dataflow is not None:
            dataflow = self.ctx.dataflow
            dataflows = self.ctx.dataflows()
            dataflow_idx = dataflows.index(dataflow)
            table.add_row(
                "Dataflow",
                str(dataflow_idx),
                f"[dataflow]{escape(dataflow.id)}[/]",
                escape(self._localize(dataflow.name)),
                escape(self._localize(dataflow.description)),
            )

            dimensions = self.ctx.key_dimensions()
            for dimension_id, dimension_codes in self.ctx.key_codes.items():
                if not dimension_codes and (
                    self.dimension is None or dimension_id != self.dimension.id
                ):
                    continue

                (dimension_idx, dimension) = next(
                    x for x in enumerate(dimensions) if x[1].id == dimension_id
                )
                concept = dimension.concept_identity
                table.add_row(
                    "Dimension",
                    str(dimension_idx),
                    f"[dimension]{escape(dimension_id)}[/]",
                    escape(self._localize(concept.name)),
                    escape(self._localize(concept.description)),
                )

                if not dimension_codes:
                    continue

                codes = self.ctx.codes(dimension)
                for code in sorted(dimension_codes):
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

    def do_list(self):
        if self.ctx.client.source is NoSource:
            self._list_sources()
        elif self.ctx.dataflow is None:
            self._list_dataflows()
        elif self.dimension is None:
            self._list_dimensions()
        else:
            self._list_codes()

    def _list_sources(self):
        # Define table.
        table = Table(
            show_edge=True,
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
        dataflows = self.ctx.dataflows()

        # Define table.
        table = Table(
            show_edge=True,
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
        for idx, dataflow in enumerate(dataflows):
            table.add_row(
                str(idx),
                escape(dataflow.id),
                escape(self._localize(dataflow.name)),
                escape(self._localize(dataflow.description)),
            )

        # Display table.
        self._print_table(table)

    def _list_dimensions(self):
        dimensions = self.ctx.key_dimensions()

        # Define table.
        table = Table(
            show_edge=True,
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
        for idx, dimension in enumerate(dimensions):
            concept = dimension.concept_identity
            table.add_row(
                str(idx),
                escape(dimension.id),
                escape(self._localize(concept.name)),
                escape(self._localize(concept.description)),
            )

        # Display table.
        self._print_table(table)

    def _list_codes(self):
        codes = self.ctx.codes(self.dimension)

        # Define table.
        table = Table(
            show_edge=True,
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

    def do_preview(self):
        if self.ctx.version().value < 3:
            self._print_error(
                f"[source]{escape(self.ctx.client.source.id)}[/] does not support previewing data."
            )
            return

        df = self.ctx.data(limit=10)
        self.console.print(df)

    def do_save(self):
        save_query(self.ctx.query())
        self.console.print(f"Saved query: [b]{self.ctx.url()}[/]")

    def do_select(self, key):
        try:
            key = int(key)
        except ValueError:
            pass

        if self.ctx.client.source is NoSource:
            self._select_source(key)
        elif self.ctx.dataflow is None:
            self._select_dataflow(key)
        elif self.dimension is None:
            self._select_dimension(key)
        else:
            self._select_code(key)

    def _select_source(self, key):
        try:
            source = self.ctx.to_source(key)
        except KeyError:
            self._print_error(f'No source found with ID "{escape(key)}"')
        except IndexError:
            self._print_error(
                f"No source found at index {key} (should be in range 0-{len(self.ctx.sources()) - 1})"
            )
        else:
            self.ctx.select_source(source)
            self.console.print(
                f"Selected source: [source]{escape(self.ctx.client.source.id)}[/]"
            )

    def _select_dataflow(self, key):
        try:
            dataflow = self.ctx.to_dataflow(key)
        except KeyError:
            self._print_error(f'No dataflow found with ID "{escape(key)}"')
        except IndexError:
            self._print_error(
                f"No dataflow found at index {key} (should be in range 0-{len(self.ctx.dataflows()) - 1})"
            )
        else:
            self.ctx.select_dataflow(dataflow)
            # Pre-fetch datastructure so that `self._prompt` can get the number of dimensions.
            self.ctx.get_datastructure()
            self.console.print(
                f"Selected dataflow: [dataflow]{escape(self.ctx.dataflow.id)}[/]"
            )

    def _select_dimension(self, key):
        try:
            dimension = self.ctx.to_key_dimension(key)
        except KeyError:
            self._print_error(f'No dimension found with ID "{escape(key)}"')
        except IndexError:
            self._print_error(
                f"No dimension found at index {key} (should be in range 0-{len(self.ctx.key_dimensions()) - 1})"
            )
        else:
            self.dimension = dimension
            self.console.print(
                f"Selected dimension: [dimension]{escape(dimension.id)}[/]"
            )

    def _select_code(self, key):
        if key == "*":
            self.ctx.clear_codes(self.dimension)
            self.console.print(
                f"Cleared all codes from [dimension]{self.dimension.id}[/]"
            )
            return

        try:
            code = self.ctx.to_code(self.dimension, key)
        except KeyError:
            self._print_error(f'No code found with ID "{escape(key)}"')
        except IndexError:
            self._print_error(
                f"No code found at index {key} (should be in range 0-{len(self.ctx.codes(self.dimension)) - 1})"
            )
        else:
            if self.ctx.toggle_code(self.dimension, code):
                self.console.print(
                    f"Added [code]{escape(code.id)}[/] to [dimension]{escape(self.dimension.id)}"
                )
            else:
                self.console.print(
                    f"Removed [code]{escape(code.id)}[/] from [dimension]{escape(self.dimension.id)}"
                )

    def _suggest_commands(self):
        commands = ["help", "quit", "list"]
        if self.ctx.client.source is not NoSource:
            commands.extend(["info", "back"])
        if self.ctx.dataflow is not None:
            commands.append("save")
        commands = ", ".join(commands)

        self.console.print(f"Commands: {commands}", style="help")

    def _print_error(self, msg):
        self.console.print(f"[error]Error:[/] {msg}", highlight=True)

    def _print_table(self, table):
        if table.row_count == 0:
            self.console.print("No results found")
        elif table.row_count <= self.max_unpaged_rows:
            self.console.print(table)
        else:
            with self.console.pager(styles=True, links=True):
                self.console.print(table)

    def _localize(self, s):
        return s.localized_default(self.locale)

    def _child_resource_str(self):
        if self.ctx.client.source is NoSource:
            return "source", "sources"
        elif self.ctx.dataflow is None:
            return "dataflow", "dataflows"
        elif self.dimension is None:
            return "dimension", "dimensions"
        else:
            return "code", "codes"
