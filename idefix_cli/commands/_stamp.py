import json

from idefix_cli._commons import get_git_data
from idefix_cli._commons import requires_idefix


def _add_stamp_args(parser):
    parser.add_argument(
        "-d",
        "--json",
        dest="todict",
        action="store_true",
        help="print to JSON serializable format.",
    )


@requires_idefix()
def stamp(todict: bool = False) -> int:
    """
    Print idefix latest version tag-(git hash) and current time to stdout.
    """
    data = get_git_data()
    if todict:
        text = json.dumps(data, indent=2)
    else:
        text = "\n".join(list(data.values()))

    print(text)
    return 0
