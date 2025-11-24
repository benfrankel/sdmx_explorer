def _init():
    # `readline` is not available on Windows.
    try:
        import readline  # noqa: F401
    except ImportError:
        pass

    _patch()
    _init_logging()


def _init_logging():
    from rich.logging import RichHandler
    from .display import CONSOLE
    import logging

    logging.getLogger().handlers = [
        RichHandler(
            console=CONSOLE,
            rich_tracebacks=True,
            omit_repeated_times=False,
        ),
    ]


def _patch():
    """Monkey patch to fix upstream bugs."""
    import rich.console
    from getpass import getpass

    # Workaround for <https://github.com/Textualize/rich/issues/2293>.
    class _ConsoleWithInputBackspaceFixed(rich.console.Console):
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

    rich.console.Console = _ConsoleWithInputBackspaceFixed


_init()
