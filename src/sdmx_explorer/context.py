from rich.markup import escape
import sdmx
from sdmx.model import TimeDimension
from sdmx.source import NoSource

import logging

from .query import Query


class SdmxContext:
    def __init__(self, client=None, console=None):
        if client is None:
            client = sdmx.Client()
        self.client = client
        self.console = console
        self.dataflow = None
        self.codes = None

    def reset(self):
        self.client.source = NoSource
        self.dataflow = None
        self.codes = None

    def back(self):
        if self.dataflow is not None:
            self.dataflow = None
            self.codes = None
        elif self.client.source is not NoSource:
            self.client.source = NoSource
        else:
            return False
        return True

    def select_source(self, source):
        self.client.source = source
        self.dataflow = None
        self.codes = None

    def select_dataflow(self, dataflow):
        if self.client.source is NoSource:
            raise MissingSelectionError("No source selected")
        self.dataflow = dataflow
        self.codes = dict()

    def toggle_code(self, dimension, code):
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")

        self.codes.setdefault(dimension.id, set()).symmetric_difference_update(code)
        return code in self.codes[dimension.id]

    def clear_codes(self, dimension):
        self.codes.get(dimension.id, set()).clear()

    def url(self):
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")

        req = self.get(
            resource_type="data",
            resource_id=self.dataflow.id,
            key=self.key(),
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
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")

        return Query(
            source=self.client.source.id,
            dataflow=self.dataflow.id,
            key=self.key(),
        )

    def key(self, rich=False, selected_dimension=None):
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")

        dsd = self.get_datastructure()
        dimensions = []
        for dimension in dsd.dimensions.components:
            if isinstance(dimension, TimeDimension):
                continue

            codes = sorted(self.codes.get(dimension.id, set()))
            if codes:
                s = "+".join(
                    f"[code]{escape(code.id)}[/]" if rich else code.id for code in codes
                )
            else:
                s = "*"

            # Show the selected dimension.
            if selected_dimension is not None and dimension.id == selected_dimension.id:
                s = (
                    f"[u][dimension]{escape(dimension.id)}[/]={s}[/]"
                    if rich
                    else f"{dimension.id}={s}"
                )

            dimensions.append(s)
        return ".".join(dimensions)

    def get_dataflows(self):
        if self.client.source is NoSource:
            raise MissingSelectionError("No source selected")
        if not self.client.source.supports["dataflow"]:
            raise UnsupportedQueryError('Source does not support "dataflow" queries')

        msg = self.get(resource_type="dataflow")
        return sorted(msg.dataflow.values())

    def get_datastructure(self):
        if self.dataflow is None:
            raise MissingSelectionError("No dataflow selected")
        if not self.client.source.supports["datastructure"]:
            raise UnsupportedQueryError(
                'Source does not support "datastructure" queries'
            )

        dsd = self.dataflow.structure
        msg = self.get(
            resource_type="datastructure",
            resource_id=dsd.id,
            agency_id=dsd.maintainer.id,
            references="children",
        )
        return msg.structure[dsd.id]

    def get_dimensions(self):
        return self.get_datastructure().dimensions.components

    def get_key_dimensions(self):
        return [x for x in self.get_dimensions() if not isinstance(x, TimeDimension)]

    def get_codelist(self, dimension):
        representation = (
            dimension.local_representation
            or dimension.concept_identity.core_representation
        )
        codelist = representation.enumerated
        if codelist is None:
            raise ValueError("No codelist associated with the given dimension")

        if self.client.source is NoSource:
            raise MissingSelectionError("No source selected")
        if not self.client.source.supports["codelist"]:
            raise UnsupportedQueryError('Source does not support "codelist" queries')

        msg = self.get(
            resource_type="codelist",
            resource_id=codelist.id,
            agency_id=codelist.maintainer.id,
        )
        return sorted(msg.codelist[codelist.id].items.values())

    def get_data(self):
        return self.query().data(self.client)

    # TODO: Fix upstream and simplify this workaround.
    def get(self, **kwargs):
        # TODO: Fix `dry_run=True` still logging (info).
        old_level = sdmx.log.level
        sdmx.log.setLevel(logging.FATAL + 1)

        dry_run_kwargs = dict(kwargs)
        dry_run_kwargs["dry_run"] = True
        # TODO: Fix `dry_run` + `use_cache` returning the cache hit instead of returning the request.
        dry_run_kwargs["use_cache"] = False
        req = self.client.get(**dry_run_kwargs)

        sdmx.log.setLevel(old_level)

        if kwargs.get("dry_run", False):
            return req

        if req.url in self.client.cache:
            return self.client.cache[req.url]

        kwargs["use_cache"] = True
        if self.console is None:
            msg = self.client.get(**kwargs)
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
