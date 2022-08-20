import argparse
import os
import re
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from idefix_cli._main import _setup_commands
from idefix_cli._main import main

SRC_DIR = Path(__file__).parents[1].joinpath("idefix_cli")


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="plugin system tests are broken on windows"
)
@pytest.mark.parametrize(
    "content, msg",
    (
        (("\n"), " is missing required functions " "'command' and 'add_arguments'"),
        (
            ("def add_arguments():\n", "    return\n"),
            " is missing a 'command' function",
        ),
        (
            ("def command():\n", "    return\n"),
            " is missing a 'add_arguments' function",
        ),
        (
            (
                "def add_arguments():\n",
                "    return\n",
                "def command():\n",
                "    return\n",
            ),
            ".add_arguments function's signature is invalid. "
            "Expected a single argument named 'parser', found []",
        ),
        (
            (
                "def add_arguments(parser):\n",
                "    return\n",
                "def command():\n",
                "    return\n",
            ),
            " is missing a module docstring",
        ),
    ),
)
def test_broken_command_plugin(content, msg):
    with NamedTemporaryFile(
        mode="w", dir=str(SRC_DIR / "_commands"), suffix=".py"
    ) as fh:
        fh.writelines(content)
        fh.seek(0)  # force flush
        module_name, _ = os.path.splitext(os.path.basename(fh.name))
        with pytest.raises(
            RuntimeError,
            match=re.escape(f"command plugin {module_name}{msg}"),
        ):
            _setup_commands(argparse.ArgumentParser())


def test_unknown_args(capsys):
    args = "--an_invalid_argument", "-another"
    ret = main(["clean", *args])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"💥 received unknown arguments {args!r}\n"
