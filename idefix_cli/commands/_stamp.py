import json
import os
from datetime import datetime
from getpass import getuser
from socket import gethostname
from time import ctime

import git

from idefix_cli._commons import requires_idefix


def _add_stamp_args(parser):
    parser.add_argument(
        "-d",
        "--json",
        dest="todict",
        action="store_true",
        help="print to JSON serializable format.",
    )


@requires_idefix
def stamp(todict: bool = False):
    """
    Print idefix latest version tag-(git hash) and current time to stdout.
    """
    repo = git.Repo(os.environ["IDEFIX_DIR"])
    data = {
        "tag": str(repo.tags[-1]),
        "sha": repo.head.object.hexsha,
        "user": getuser(),
        "host": gethostname(),
        "date": ctime(datetime.now().timestamp()),
    }

    if todict:
        text = json.dumps(data, indent=2)
    else:
        text = "\n".join(list(data.values()))

    print(text)
    return 0
