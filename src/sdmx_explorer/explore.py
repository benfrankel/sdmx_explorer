from . import init

init.init()

from . import queries

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

# `readline` is not available on Windows.
try:
    import readline
except ImportError:
    pass

log = logging.getLogger(__name__)


class SdmxExplorer:
    def __init__(self):
        # SDMX context:
        self.client = sdmx.Client(expire_after=timedelta(days=1))
        self.selected_dataflow = None
        self.selected_dimension = None
        self.selected_codes = dict()

        # Display:
        self.locale = "en"
        self.verbose = False
        self.max_unpaged_rows = 12
        theme = {
            "help": "italic purple",
            "error": "bold red",
            "index": "bold purple",
            "source": "bold yellow",
            "dataflow": "bold green",
            "dimension": "bold blue",
            "code": "bold magenta",
        }
        self.console = Console(theme=Theme(theme), highlight=False)

    def repl(self):
        self._display_welcome()
        while self.client is not None:
            try:
                self._display_commands()
                command = self._prompt()
                self._dispatch(command)
            except KeyboardInterrupt:
                self.console.print("Interrupted")
            except Exception as err:
                if self.verbose:
                    self.console.print_exception(show_locals=True)
                else:
                    self._print_error(f"{err!r}")
            self.console.print()

    def _prompt(self):
        path = self._get_selection_path(rich=True, selected_dimension=True)
        prefix = f"{path}> "

        try:
            return self.console.input(prefix).strip()
        except EOFError:
            if self.client.source is not NoSource:
                self.console.print()
            return "back"
        except BaseException as err:
            self.console.print()
            raise err

    def _dispatch(self, command):
        match command:
            case "":
                pass
            case "help" | "h" | "?":
                self._display_help()
            case "verbose" | "v":
                self._toggle_verbose()
            case "clear" | "c":
                self._clear_cache()
            case "quit" | "q" | "exit" | "end" | "stop":
                self._quit()
            case "back" | "b":
                self._back()
            case "info" | "i":
                self._display_info()
            case "list" | "ls" | "l":
                self._list()
            case "data" | "d":
                self._get_data()
            case "save" | "s":
                self._save_query()
            case _:
                try:
                    self._select(command)
                except KeyError:
                    self._print_error(
                        f'Invalid command or selection "{escape(command)}".'
                    )

    def _toggle_verbose(self, quiet=False):
        self.verbose = not self.verbose
        level = logging.INFO if self.verbose else logging.WARN
        log.setLevel(level)
        sdmx.log.setLevel(level)
        if not quiet:
            self.console.print(f"Verbose: [bold]{self.verbose}[/]", highlight=True)

    def _clear_cache(self):
        self.client.clear_cache()
        requests_cache.clear()
        self.console.print("Cache cleared")

    def _quit(self):
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
            self._quit()

    def _display_info(self):
        if self.client.source is NoSource:
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
        url = self._get_selection_url(quiet=True)
        if url is not None:
            path = self._get_selection_path(rich=True, selected_dimension=False)
            table.add_row(
                "Query",
                "",
                path,
                "Currently selected",
                f"[dim][link {url}]{escape(url)}[/][/]",
            )

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
            dataflows = sorted(self._get_dataflows().values())
            dataflow_idx = dataflows.index(self.selected_dataflow)
            table.add_row(
                "Dataflow",
                str(dataflow_idx),
                f"[dataflow]{escape(self.selected_dataflow.id)}[/]",
                escape(self._localize(self.selected_dataflow.name)),
                escape(self._localize(self.selected_dataflow.description)),
            )

            dimensions = self._get_dimensions()
            for dimension_id, dimension_codes in self.selected_codes.items():
                if not dimension_codes and (
                    self.selected_dimension is None
                    or dimension_id != self.selected_dimension.id
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

                codes = self._get_codes(dimension=dimension)
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
        dataflows = self._get_dataflows()
        if dataflows is None:
            return

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
        dimensions = self._get_dimensions()
        if dimensions is None:
            return

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
        codes = self._get_codes()
        if codes is None:
            return

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

    def _select(self, key):
        if self.client.source is NoSource:
            self._select_source(key)
        elif self.selected_dataflow is None:
            self._select_dataflow(key)
        elif self.selected_dimension is None:
            self._select_dimension(key)
        else:
            self._select_code(key)

    def _select_source(self, key):
        sources = sdmx.list_sources()

        try:
            index = int(key)
        except ValueError:
            try:
                self.client.source = sdmx.get_source(key)
            except KeyError:
                raise KeyError(f'Source with ID "{key}" was not found')
        else:
            if not 0 <= index < len(sources):
                raise IndexError(
                    f'Source index "{index}" is not in range (0-{len(sources)})'
                )
            self.client.source = sdmx.get_source(sources[index])

        self.console.print(
            f"Selected source: [source]{escape(self.client.source.id)}[/]"
        )

    def _select_dataflow(self, key):
        dataflows = self._get_dataflows()
        if dataflows is None:
            return False

        try:
            index = int(key)
        except ValueError:
            try:
                self.selected_dataflow = dataflows[key]
            except KeyError:
                raise KeyError(f'Dataflow with ID "{key}" was not found')
        else:
            if not 0 <= index < len(dataflows):
                raise IndexError(
                    f'Dataflow index "{index}" is not in range (0-{len(dataflows)})'
                )
            self.selected_dataflow = sorted(dataflows.values())[index]

        # Pre-fetch dimensions so that `self._prompt` can get the number of dimensions.
        self._get_dimensions()

        self.console.print(
            f"Selected dataflow: [dataflow]{escape(self.selected_dataflow.id)}[/]"
        )

    def _select_dimension(self, key):
        dimensions = self._get_dimensions()
        if dimensions is None:
            return False

        try:
            index = int(key)
        except ValueError:
            try:
                self.selected_dimension = next(x for x in dimensions if x.id == key)
            except StopIteration:
                raise KeyError(f'Dimension with ID "{key}" was not found')
        else:
            if not 0 <= index < len(dimensions):
                raise IndexError(
                    f'Dimension index "{index}" is not in range (0-{len(dimensions)})'
                )
            self.selected_dimension = dimensions[index]

        self.console.print(
            f"Selected dimension: [dimension]{escape(self.selected_dimension.id)}[/]"
        )

    def _select_code(self, key):
        codes = self._get_codes()
        if codes is None:
            return False

        if key == "*":
            self.selected_codes[self.selected_dimension.id] = set()
            self.console.print(
                f"Cleared all codes from [dimension]{self.selected_dimension.id}[/]"
            )
            return

        try:
            index = int(key)
        except ValueError:
            try:
                code = next(x for x in codes if x.id == key)
            except StopIteration:
                raise KeyError(f'Code with ID "{key}" was not found')
        else:
            if not 0 <= index < len(codes):
                raise IndexError(
                    f'Code index "{index}" is not in range (0-{len(codes)})'
                )
            code = codes[index]

        dim_codes = self.selected_codes.setdefault(self.selected_dimension.id, set())
        dim_codes.symmetric_difference_update(code)

        if code in dim_codes:
            self.console.print(
                f"Added [code]{escape(code.id)}[/] to [dimension]{escape(self.selected_dimension.id)}"
            )
        else:
            self.console.print(
                f"Removed [code]{escape(code.id)}[/] from [dimension]{escape(self.selected_dimension.id)}"
            )

    def _get_dataflows(self, quiet=False):
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

    def _get_dimensions(self, quiet=False):
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
            # TODO: Workaround for <https://github.com/khaeru/sdmx/issues/259>.
            params={"references": "children"},
        )
        if msg is None:
            return

        dsd = msg.structure[dsd.id]
        return [
            dim for dim in dsd.dimensions.components if type(dim) is not TimeDimension
        ]

    def _get_codes(self, dimension=None, quiet=False):
        if not self.client.source.supports["codelist"]:
            if not quiet:
                self._print_error(
                    f"[source]{self.client.source.id}[/] does not support listing codes."
                )
            return
        if dimension is None:
            dimension = self.selected_dimension
        if dimension is None:
            return

        representation = (
            dimension.local_representation
            or dimension.concept_identity.core_representation
        )
        codelist = representation.enumerated
        if codelist is None:
            if not quiet:
                self._print_error(
                    f"[dimension]{dimension.id}[/] does not have a codelist."
                )
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

    def _get_selection_key(self, rich=False, selected_dimension=False, quiet=False):
        if self.selected_dataflow is None:
            if not quiet:
                self._print_error("No dataflow selected.")
            return

        key = []
        for dim in self._get_dimensions() or []:
            dim_codes = self.selected_codes.setdefault(dim.id, set())
            if dim_codes:
                s = "+".join(
                    f"[code]{escape(code.id)}[/]" if rich else code.id
                    for code in sorted(dim_codes)
                )
            else:
                s = "*"

            # Underline the selected dimension's codes.
            if (
                rich
                and selected_dimension
                and self.selected_dimension is not None
                and self.selected_dimension.id == dim.id
            ):
                s = f"[u]{s}[/]"
            key.append(s)
        key = ".".join(key)

        return key

    def _get_selection_path(self, rich=False, selected_dimension=False):
        path = []
        if self.client.source is not NoSource:
            path = [
                f"[source]{escape(self.client.source.id)}[/]"
                if rich
                else self.client.source.id
            ]
        if self.selected_dataflow is not None:
            key = self._get_selection_key(
                rich=rich,
                selected_dimension=selected_dimension,
                quiet=True,
            )
            path.append(
                f"[dataflow]{escape(self.selected_dataflow.id)}[/]({key})"
                if rich
                else f"{self.selected_dataflow.id}({key})"
            )
        if selected_dimension and self.selected_dimension is not None:
            path.append(
                f"[dimension]{escape(self.selected_dimension.id)}[/]"
                if rich
                else self.selected_dimension.id
            )
        path = "/".join(path)

        return path

    def _get_selection_url(self, quiet=False):
        key = self._get_selection_key(quiet=quiet)
        if key is None:
            return

        req = self._get(
            "data",
            resource_type="data",
            resource_id=self.selected_dataflow.id,
            key=key,
            dry_run=True,
        )
        return req.url

    def _get_data(self, quiet=False):
        if self.selected_dataflow is None:
            if not quiet:
                self._print_error("No dataflow selected.")
            return

        key = []
        for dim in self._get_dimensions() or []:
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

    def _get(self, target, **kwargs):
        # TODO: Open an issue for `dry_run=True` still logging. This is a workaround to get the URL without logging.
        if self.verbose:
            self._toggle_verbose(quiet=True)
            new_kwargs = dict(kwargs)
            new_kwargs["dry_run"] = True
            req = self.client.get(**new_kwargs)
            self._toggle_verbose(quiet=True)
        else:
            new_kwargs = dict(kwargs)
            new_kwargs["dry_run"] = True
            req = self.client.get(**new_kwargs)
        if req.url in self.client.cache:
            return self.client.cache[req.url]

        if kwargs.get("dry_run", False):
            return req

        with self.console.status(
            f"Fetching {target}: [dim][link {req.url}]{escape(req.url)}[/][/]"
        ):
            msg = self.client.get(use_cache=True, **kwargs)

        # TODO: Workaround for <https://github.com/khaeru/sdmx/issues/256>.
        self.client.cache[req.url] = msg
        return msg

    def _save_query(self):
        url = self._get_selection_url()
        if url is None:
            return

        queries.save(url)

        self.console.print(f"Saved query: [b]{url}[/]")

    def _display_welcome(self):
        self.console.print("SDMX Explorer", style="bold purple")

    def _display_help(self):
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
            "list, l",
            f"List {children} [dim](aliases: ls)[/]",
        )
        table.add_row(
            "info, i",
            "Show information on the current selection",
        )
        table.add_row(
            "data, d",
            "Download data",
        )
        table.add_row(
            "save, s",
            "Save the current query",
        )
        table.add_row(
            "back, b",
            "Navigate up",
        )
        table.add_row(
            "quit, q",
            "Quit the session [dim](aliases: exit, end, stop)[/]",
        )
        table.add_row(
            "<INDEX>, <ID>",
            f"Select a {child}",
        )

        # Display table.
        self._print_table(table)

    def _display_commands(self):
        commands = ["help", "quit", "list"]
        if self.client.source is not NoSource:
            commands.extend(["info", "back"])
        if self.selected_dataflow is not None:
            commands.extend(["data", "save"])
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
        if self.client.source is NoSource:
            return "source", "sources"
        elif self.selected_dataflow is None:
            return "dataflow", "dataflows"
        elif self.selected_dimension is None:
            return "dimension", "dimensions"
        else:
            return "code", "codes"


def main():
    SdmxExplorer().repl()


if __name__ == "__main__":
    main()
