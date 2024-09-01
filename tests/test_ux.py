import pytest
from pytest_check import check

from idefix_cli.__main__ import main

HELP_MESSAGE = (
    "usage: idfx [-h] [-v] {clean,clone,conf,digest,read,run,switch,write} ...\n"
    "\n"
    "options:\n"
    "  -h, --help            show this help message and exit\n"
    "  -v, --version         show program's version number and exit\n"
    "\n"
    "commands:\n"
    "  {clean,clone,conf,digest,read,run,switch,write}\n"
    "    clean               remove compilation files\n"
    "    clone               clone a problem directory\n"
    "    conf                configure Idefix\n"
    "    digest              agregate performance data from log files as json\n"
    "    read                read an Idefix inifile and print it to json format\n"
    "    run                 run an Idefix problem\n"
    "    switch              switch git branch in $IDEFIX_DIR using git checkout\n"
    "    write               write an Idefix inifile from a json string\n"
)


def get_lines(help_message: str) -> list[str]:
    # skip the first lines because they differ between macos and linux
    lines = iter(help_message.splitlines())
    while not next(lines).startswith("options:"):
        continue

    return list(lines)


@pytest.mark.usefixtures("isolated_conf_dir")
def test_no_command_passed(capsys):
    ret = main([])
    with check:
        assert ret != 0
    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert get_lines(err) == get_lines(HELP_MESSAGE)
