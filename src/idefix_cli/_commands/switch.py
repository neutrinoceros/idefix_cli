"""switch git branch in $IDEFIX_DIR using git checkout"""

import os
from pathlib import Path

from idefix_cli.lib import print_error, requires_idefix, run_subcommand


def add_arguments(parser):
    parser.add_argument(
        "branch",
        default="-",
        nargs="?",
        help=(
            "the name of the branch to switch to. "
            "If unspecified, switch the most recently visited other branch"
        ),
    )


@requires_idefix()
def command(branch: str) -> int:
    idefix_dir = Path(os.environ["IDEFIX_DIR"]).resolve()
    if not idefix_dir.joinpath(".git").is_dir():
        print_error("$IDEFIX_DIR doesn't point to a git repository")
        return 1
    return run_subcommand(["git", "checkout", branch], loc=idefix_dir)
