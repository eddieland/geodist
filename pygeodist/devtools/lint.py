import subprocess
from typing import TYPE_CHECKING, Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

if TYPE_CHECKING:

    def log_calls(*args: object, **kwargs: object) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Typed stub for funlog.log_calls decorator."""
        ...
else:
    from funlog import log_calls
from rich import get_console, reconfigure
from rich import print as rprint

# Update as needed.
SRC_PATHS = ["src", "tests", "devtools"]
DOC_PATHS = ["README.md"]


reconfigure(emoji=not get_console().options.legacy_windows)  # No emojis on legacy windows.


def main() -> int:
    """Run lint commands and return count of failures."""
    rprint()

    errcount = 0
    errcount += run(["codespell", "--write-changes", *SRC_PATHS, *DOC_PATHS])
    errcount += run(["ruff", "check", "--fix", *SRC_PATHS])
    errcount += run(["ruff", "format", *SRC_PATHS])
    errcount += run(["mypy", *SRC_PATHS])

    rprint()

    if errcount != 0:
        rprint(f"[bold red]:x: Lint failed with {errcount} errors.[/bold red]")
    else:
        rprint("[bold green]:white_check_mark: Lint passed![/bold green]")
    rprint()

    return errcount


@log_calls(level="warning", show_timing_only=True)
def run(cmd: list[str]) -> int:
    rprint()
    rprint(f"[bold green]>> {' '.join(cmd)}[/bold green]")
    errcount = 0
    try:
        subprocess.run(cmd, text=True, check=True)
    except KeyboardInterrupt:
        rprint("[yellow]Keyboard interrupt - Cancelled[/yellow]")
        errcount = 1
    except subprocess.CalledProcessError as e:
        rprint(f"[bold red]Error: {e}[/bold red]")
        errcount = 1

    return errcount


if __name__ == "__main__":
    exit(main())
