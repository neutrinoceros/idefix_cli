import os
import subprocess
import sys

from idefix_cli._commons import print_err, print_warning, requires_idefix


def wrap_outputs(stdout, stderr) -> None:
    if out := stdout.decode():
        print(out)

    if err := stderr.decode():
        for line in err.splitlines():
            if line.startswith("Error:"):
                print_err(line.removeprefix("Error:").strip())
            elif line.startswith("Warning:"):
                print_warning(line.removeprefix("Warning:").strip())
            else:
                print(line, file=sys.stderr)


@requires_idefix()
def setup(args) -> int:
    cmd = ["python3", os.path.join(os.environ["IDEFIX_DIR"], "configure.py"), *args]
    ret = subprocess.run(cmd, capture_output=True)
    wrap_outputs(ret.stdout, ret.stderr)
    return ret.returncode
