import json
import os
from collections import OrderedDict
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
    data = (
        OrderedDict()
    )  # support old versions of python where dict doesn't retain entries order
    repo = git.Repo(os.getenv("IDEFIX_DIR"))

    data["tag"] = repo.tags[-1]
    data["sha"] = repo.head.object.hexsha
    data["date"] = ctime(datetime.now().timestamp())
    data["host"] = gethostname()
    data["user"] = getuser()
    if todict:
        text = json.dumps(data, indent=2)
    else:
        text = "\n".join(list(data.values()))

    print(text)
    return 0
