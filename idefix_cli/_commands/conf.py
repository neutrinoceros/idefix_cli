"""setup an Idefix problem"""
from __future__ import annotations

import os
from typing import NoReturn

from idefix_cli._commons import requires_idefix

parser_kwargs = dict(
    add_help=False
)  # because it's a wrapper, we want to pass down even the "--help" flag


def add_arguments(parser):
    "Nothing to do here, this command is a pure wrapper"
    return


@requires_idefix()
def command(args) -> NoReturn:
    cmd = ["python3", os.path.join(os.environ["IDEFIX_DIR"], "configure.py"), *args]
    os.execvp(cmd[0], cmd)
