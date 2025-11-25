from rich.markup import escape
import sdmx
from sdmx.model import TimeDimension
from sdmx.source import NoSource

from .query import Query


class SdmxContext:
    def __init__(self, client=None, console=None):
        if client is None:
            client = sdmx.Client()
        self.client = client
        self.console = console
        self.dataflow = None
        self.key_codes = None

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path()!r})"

    def to_source(self, source):
        if isinstance(source, sdmx.source.Source):
            return source
        elif isinstance(source, str):
            return sdmx.get_source(source)
        elif isinstance(source, int):
            if source < 0:
                raise IndexError()
            return sdmx.get_source(sdmx.list_sources()[source])
        else:
            raise TypeError(f"Unexpected type: {type(source)}")

    def to_dataflow(self, dataflow):
        if isinstance(dataflow, sdmx.model.common.BaseDataflow):
            return dataflow
        elif isinstance(dataflow, str):
            msg = self.get_dataflow()
            return msg.dataflow[dataflow]
        elif isinstance(dataflow, int):
            if dataflow < 0:
                raise IndexError()
            return self.dataflows()[dataflow]
        else:
            raise TypeError(f"Unexpected type: {type(dataflow)}")

    def to_key_dimension(self, dimension):
        if isinstance(dimension, sdmx.model.common.Dimension) and not isinstance(
            dimension, TimeDimension
        ):
            return dimension
        elif isinstance(dimension, str):
            return next(x for x in self.key_dimensions() if x.id == dimension)
        elif isinstance(dimension, int):
            if dimension < 0:
                raise IndexError()
            return self.key_dimensions()[dimension]
        else:
            raise TypeError(f"Unexpected type: {type(dimension)}")

    def to_dimension(self, dimension):
        if isinstance(dimension, sdmx.model.common.Dimension):
            return dimension
        elif isinstance(dimension, str):
            return next(x for x in self.dimensions() if x.id == dimension)
        elif isinstance(dimension, int):
            if dimension < 0:
                raise IndexError()
            return self.dimensions()[dimension]
        else:
            raise TypeError(f"Unexpected type: {type(dimension)}")

    def to_code(self, dimension, code):
        dimension = self.to_dimension(dimension)
        if isinstance(code, sdmx.model.common.Code):
            return code
        elif isinstance(code, str):
            msg = self.get_codelist(dimension)
            return next(iter(msg.codelist.values())).items[code]
        elif isinstance(code, int):
            if code < 0:
                raise IndexError()
            return self.codes(dimension)[code]
        else:
            raise TypeError(f"Unexpected type: {type(dimension)}")

    def reset(self):
        self.client.source = NoSource
        self.dataflow = None
        self.key_codes = None

    def back(self):
        if self.dataflow is not None:
            self.dataflow = None
            self.key_codes = None
        elif self.client.source is not NoSource:
            self.client.source = NoSource
        else:
            return False
        return True

    def select_query(self, query):
        old_source = self.client.source
        old_dataflow = self.dataflow
        old_key_codes = self.key_codes
        try:
            self.select_source(query.source)
            self.select_dataflow(query.dataflow)
            self.key_codes = dict()

            key_dimensions = self.key_dimensions()
            key_codes = query.key.split(".")
            if len(key_codes) != len(key_dimensions):
                raise ValueError(
                    f"Query key has {len(key_codes)} dimensions; expected {len(key_dimensions)}"
                )
            for dimension, codes in zip(key_dimensions, key_codes):
                if codes == "*":
                    continue
                self.key_codes[dimension] = set(
                    self.to_code(dimension, code) for code in codes.split("+")
                )
        except BaseException:
            self.client.source = old_source
            self.dataflow = old_dataflow
            self.key_codes = old_key_codes
            raise

    def select_source(self, source):
        self.reset()
        self.client.source = self.to_source(source)

    def select_dataflow(self, dataflow):
        if self.client.source is NoSource:
            raise MissingSelectionError("No source selected")

        self.dataflow = self.to_dataflow(dataflow)
        self.key_codes = dict()

    def toggle_code(self, dimension, code):
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")

        dimension = self.to_key_dimension(dimension)
        self.key_codes.setdefault(dimension.id, set()).symmetric_difference_update(code)
        return code in self.key_codes[dimension.id]

    def clear_codes(self, dimension):
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")

        dimension = self.to_key_dimension(dimension)
        self.key_codes.get(dimension.id, set()).clear()

    def url(self):
        key = self.key()
        req = self.get(
            resource_type="data",
            resource_id=self.dataflow.id,
            key=key,
            dry_run=True,
        )
        return req.url

    def path(self, rich=False, selected_dimension=None):
        parts = []
        if self.client.source is not NoSource:
            id = self.client.source.id
            parts.append(f"[source]{escape(id)}[/]" if rich else id)
        if self.dataflow is not None:
            id = self.dataflow.id
            parts.append(f"[dataflow]{escape(id)}[/]" if rich else id)
            parts.append(self.key(rich=rich, selected_dimension=selected_dimension))
        return "/".join(parts)

    def query(self):
        key = self.key()
        return Query(
            source=self.client.source.id,
            dataflow=self.dataflow.id,
            key=key,
        )

    def key(self, rich=False, selected_dimension=None):
        dsd = self.datastructure()
        dimensions = []
        for dimension in dsd.dimensions.components:
            if isinstance(dimension, TimeDimension):
                continue

            codes = sorted(self.key_codes.get(dimension.id, set()))
            if codes:
                s = "+".join(
                    f"[code]{escape(code.id)}[/]" if rich else code.id for code in codes
                )
            else:
                s = "*"

            # Show the selected dimension.
            if selected_dimension is not None:
                selected_dimension = self.to_key_dimension(selected_dimension)
            if selected_dimension is not None and dimension.id == selected_dimension.id:
                s = (
                    f"[u][dimension]{escape(dimension.id)}[/]={s}[/]"
                    if rich
                    else f"{dimension.id}={s}"
                )

            dimensions.append(s)
        return ".".join(dimensions)

    def version(self):
        if self.client.source is NoSource:
            raise MissingSelectionError("No source selected")

        return max(self.client.source.versions)

    @staticmethod
    def sources():
        return [sdmx.get_source(x) for x in sdmx.list_sources()]

    def dataflows(self):
        msg = self.get_dataflow()
        return sorted(msg.dataflow.values())

    def datastructure(self):
        msg = self.get_datastructure()
        return msg.structure[self.dataflow.structure.id]

    def dimensions(self):
        return self.datastructure().dimensions.components

    def key_dimensions(self):
        return [x for x in self.dimensions() if not isinstance(x, TimeDimension)]

    def attributes(self):
        return self.datastructure().attributes.components

    def measures(self):
        return self.datastructure().measures.components

    def codes(self, dimension):
        msg = self.get_codelist(dimension)
        return sorted(next(iter(msg.codelist.values())).items.values())

    def data(self):
        msg = self.get_data()
        if msg.data[0].series:
            return sdmx.to_pandas(msg).reset_index()

    def get_dataflow(self, **kwargs):
        return self.get(
            resource_type="dataflow",
            **kwargs,
        )

    def get_datastructure(self, **kwargs):
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")

        dsd = self.dataflow.structure
        return self.get(
            resource_type="datastructure",
            resource_id=dsd.id,
            agency_id=dsd.maintainer.id,
            references="children",
            **kwargs,
        )

    def get_codelist(self, dimension, **kwargs):
        dimension = self.to_key_dimension(dimension)
        representation = (
            dimension.local_representation
            or dimension.concept_identity.core_representation
        )
        codelist = representation.enumerated
        if codelist is None:
            raise ValueError("No codelist associated with the given dimension")

        return self.get(
            resource_type="codelist",
            resource_id=codelist.id,
            agency_id=codelist.maintainer.id,
            **kwargs,
        )

    def get_data(self, **kwargs):
        key = self.key()
        return self.get(
            resource_type="data",
            resource_id=self.dataflow.id,
            key=key,
            **kwargs,
        )

    def get(self, **kwargs):
        if self.client.source is NoSource:
            raise MissingSelectionError("No source selected")
        resource_type = kwargs.get("resource_type")
        if not self.client.source.supports.get(resource_type, False):
            raise UnsupportedQueryError(
                f'Source does not support "{resource_type}" queries'
            )

        kwargs["use_cache"] = True
        if self.console is None or kwargs.get("dry_run", False):
            msg = self.client.get(**kwargs)
        else:
            dry_run_kwargs = dict(kwargs)
            dry_run_kwargs["dry_run"] = True
            req = self.client.get(**dry_run_kwargs)
            if req.url in self.client.cache:
                msg = self.client.cache[req.url]
            else:
                with self.console.status(
                    f"Requesting: [dim][link {req.url}]{escape(req.url)}[/][/]"
                ):
                    msg = self.client.get(**kwargs)

        if msg is None:
            raise EmptyResponseError()

        return msg


class SdmxContextError(Exception):
    """Base class for exceptions in `SdmxContext` operations."""


class UnsupportedQueryError(SdmxContextError):
    """Raised when the selected SDMX source does not support the necessary query type."""


class MissingSelectionError(SdmxContextError):
    """Raised when an SDMX source or dataflow is needed but nothing is selected."""


class EmptyResponseError(SdmxContextError):
    """Raised when an SDMX query receives an empty response."""
