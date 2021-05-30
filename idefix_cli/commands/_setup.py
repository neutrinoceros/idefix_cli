import os
from typing import NoReturn

from idefix_cli._commons import requires_idefix


@requires_idefix()
def setup(args) -> NoReturn:
    cmd = ["python3", os.path.join(os.environ["IDEFIX_DIR"], "configure.py"), *args]
    os.execvp(cmd[0], cmd)
