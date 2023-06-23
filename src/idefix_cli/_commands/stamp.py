"""print relevant data for reproduction to stdout"""
from __future__ import annotations

import json
import os
from datetime import datetime
from getpass import getuser
from socket import gethostname
from time import ctime

from packaging.version import Version

from idefix_cli.lib import get_idefix_version, print_warning, requires_idefix


@requires_idefix()
def get_git_data() -> dict[str, str]:
    data = {
        "user": getuser(),
        "host": gethostname(),
        "date": ctime(datetime.now().timestamp()),
    }
    try:
        # this import may fail in envs where the git executable is not present,
        # so we'll avoid keeping it at the top level to minimize breakage
        import git
    except ImportError as exc:
        print_warning(f"failed to load gitpython (got 'ImportError: {exc}')")
    else:
        repo = git.Repo(os.environ["IDEFIX_DIR"])
        data = {"sha": repo.head.object.hexsha, **data}
    if (version := get_idefix_version()) == Version("0"):
        version_str = "unknown version"
    else:
        version_str = str(version)
    data = {"latest ancestor version": version_str, **data}
    return data


def add_arguments(parser) -> None:
    parser.add_argument(
        "-d",
        "--json",
        dest="todict",
        action="store_true",
        help="print to JSON serializable format.",
    )


@requires_idefix()
def command(todict: bool = False) -> int:
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
