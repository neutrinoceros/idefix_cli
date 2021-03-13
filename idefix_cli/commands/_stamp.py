import json
import os
from collections import OrderedDict
from datetime import datetime
from getpass import getuser
from socket import gethostname
from subprocess import PIPE, run
from time import ctime

from idefix_helper._commons import pushd, requires_idefix


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
    with pushd(os.getenv("IDEFIX_DIR")):
        # note that this can be improved in python >= 3.7
        # where `subprocess.run` has a `text` kwarg
        # (same a `universal_newlines` but much clearer)
        # also `capture_stdout=True` can be used instead of `stdout=subprocess.PIPE`

        result = run(
            ["git", "describe", "--tags"],
            stdout=PIPE,
            check=True,
            universal_newlines=True,
        )

    data["idefix_git_tag"] = result.stdout[:-1]  # remove a newline char
    data["date"] = ctime(datetime.now().timestamp())
    data["host"] = gethostname()
    data["user"] = getuser()
    if todict:
        text = json.dumps(data, indent=2)
    else:
        text = "\n".join(list(data.values()))

    print(text)
    return 0
