import argparse
import os
import re
import sys
from tempfile import NamedTemporaryFile
from textwrap import dedent

import pytest

from idefix_cli.__main__ import _setup_commands, main
from idefix_cli.lib import print_error


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="plugin system tests are broken on windows"
)
@pytest.mark.parametrize(
    "content, msg",
    (
        (("\n"), " is missing required functions 'command' and 'add_arguments'"),
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
def test_broken_command_plugin(isolated_conf_dir, tmp_path, content, msg):
    with open(isolated_conf_dir / "idefix.cfg", "w") as fh:
        fh.write(f"[idefix_cli]\nplugins_directory = {tmp_path!s}")

    with NamedTemporaryFile(mode="w", dir=tmp_path, suffix=".py") as fh:
        fh.writelines(content)
        fh.seek(0)  # force flush
        module_name, _ = os.path.splitext(os.path.basename(fh.name))

        with pytest.raises(
            RuntimeError,
            match=re.escape(f"command plugin {module_name}{msg}"),
        ):
            _setup_commands(argparse.ArgumentParser(allow_abbrev=False))


def test_unknown_args(capsys):
    args = "--an_invalid_argument", "-another"
    ret = main(["clean", *args])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"💥 received unknown arguments {args!r}\n"


def test_plugins(isolated_conf_dir, tmp_path, capsys):
    with open(isolated_conf_dir / "idefix.cfg", "w") as fh:
        fh.write(f"[idefix_cli]\nplugins_directory = {tmp_path!s}")

    with open(tmp_path / "hello.py", "w") as fh:
        fh.write(
            dedent(
                """
                'test extension command'
                def add_arguments(parser) -> None:
                    return

                def command() -> int:
                    print('Hello Idefix !')
                    return 0
                """
            )
        )

    def _main_mock(argv):
        """A simplified version of the main function that can be trashed with no side effects on other tests"""
        parser = argparse.ArgumentParser(allow_abbrev=False)
        commands = _setup_commands(parser)

        known_args, unknown_args = parser.parse_known_args(argv)

        vargs = vars(known_args)
        cmd_name = vargs.pop("command")

        cmd, accepts_unknown_args = commands[cmd_name]
        if unknown_args and not accepts_unknown_args:
            print_error(f"received unknown arguments {tuple(unknown_args)!r}")
            return 1

        return cmd(*unknown_args, **vars(known_args))

    try:
        ret = _main_mock(["hello"])
    except SystemExit as exc:
        # SystemExit is raised by parser.parse_known_args if the command isn't found
        raise AssertionError("Command plugin wasn't found") from exc

    assert ret == 0
    out, err = capsys.readouterr()
    assert out == "Hello Idefix !\n"
    assert err == ""
