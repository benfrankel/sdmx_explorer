import requests_cache
import rich.console
from rich.logging import RichHandler
from sdmx.reader.xml.common import to_snake
from sdmx.reader.xml.v21 import Reader
from sdmx.model import common
from sdmx.reader.xml import v21

import logging

log = logging.getLogger()


def init():
    init_logging()
    init_cache()
    patch()


def init_logging():
    log.handlers = [RichHandler(rich_tracebacks=True)]


def init_cache():
    requests_cache.install_cache()


def patch():
    """Monkey patch to fix upstream bugs."""
    v21._facet = _facet
    rich.console.Console = ConsoleWithInputBackspaceFixed


# Workaround for <https://github.com/khaeru/sdmx/issues/250>.
# Adapted from <https://github.com/khaeru/sdmx/blob/71cdf849b90fb6f6fbc71786b0c1dc6e24c44a61/sdmx/reader/xml/v21.py#L580>.
@Reader.end("str:EnumerationFormat str:TextFormat")
def _facet(reader, elem):
    args = {to_snake(key): val for key, val in elem.items()}
    tt = args.pop("text_type", "String")
    try:
        fvt = common.FacetValueType[f"{tt[0].lower()}{tt[1:]}"]
    except KeyError:
        fvt = common.ExtendedFacetValueType[f"{tt[0]}{tt[1:].lower()}"]

    args.pop("is_multi_lingual", None)

    # PATCHED HERE:
    args.pop("is_multilingual", None)

    ft = common.FacetType(**args)
    reader.push(elem, common.Facet(type=ft, value_type=fvt))


# Workaround for <https://github.com/Textualize/rich/issues/2293>.
class ConsoleWithInputBackspaceFixed(rich.console.Console):
    def input(
        self,
        prompt="",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream=None,
    ) -> str:
        prompt_str = ""
        if prompt:
            with self.capture() as capture:
                self.print(prompt, markup=markup, emoji=emoji, end="")
            prompt_str = capture.get()
        if self.legacy_windows:
            self.file.write(prompt_str)
            prompt_str = ""
        if password:
            result = getpass(prompt_str, stream=stream)
        else:
            if stream:
                self.file.write(prompt_str)
                result = stream.readline()
            else:
                result = input(prompt_str)
        return result
