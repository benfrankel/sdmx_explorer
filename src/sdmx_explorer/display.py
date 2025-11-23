from rich.console import Console
from rich.theme import Theme


THEME = Theme(
    {
        "help": "italic purple",
        "error": "bold red",
        "warning": "bold yellow",
        "index": "bold purple",
        "source": "bold yellow",
        "dataflow": "bold green",
        "dimension": "bold blue",
        "code": "bold magenta",
    }
)

CONSOLE = Console(theme=THEME, highlight=False)
