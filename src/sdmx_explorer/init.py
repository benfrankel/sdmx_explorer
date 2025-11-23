import rich.console
from rich.logging import RichHandler

from getpass import getpass
import logging

from .display import CONSOLE

log = logging.getLogger()


def init():
    patch()
    init_logging()


def init_logging():
    log.handlers = [
        RichHandler(
            console=CONSOLE,
            rich_tracebacks=True,
            omit_repeated_times=False,
        ),
    ]


def patch():
    """Monkey patch to fix upstream bugs."""
    rich.console.Console = ConsoleWithInputBackspaceFixed


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
