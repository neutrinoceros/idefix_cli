import json
import os
from datetime import datetime
from getpass import getuser
from socket import gethostname
from time import ctime

from idefix_cli._commons import print_warning, requires_idefix


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
    # this import may fail in envs where the git executable is not present,
    # so we'll avoid keeping it at the top level to minimize breakage

    data = {
        "user": getuser(),
        "host": gethostname(),
        "date": ctime(datetime.now().timestamp()),
    }
    try:
        import git
    except ImportError as exc:
        print_warning(f"failed to load gitpython (got 'ImportError: {exc}')")
    else:
        repo = git.Repo(os.environ["IDEFIX_DIR"])
        data = {
            "tag": str(repo.tags[-1]),
            "sha": repo.head.object.hexsha,
        } | data

    if todict:
        text = json.dumps(data, indent=2)
    else:
        text = "\n".join(list(data.values()))

    print(text)
    return 0
