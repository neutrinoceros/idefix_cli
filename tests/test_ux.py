import sys

from pytest import assume

from idefix_cli._main import main

if sys.version_info >= (3, 10):
    OPTIONAL_SEC = "options"
else:
    OPTIONAL_SEC = "optional arguments"
HELP_MESSAGE = (
    "usage: idfx [-h] [-v] {clean,clone,conf,read,run,stamp,write} ...\n"
    "\n"
    "positional arguments:\n"
    "  {clean,clone,conf,read,run,stamp,write}\n"
    "    clean               remove compilation files\n"
    "    clone               clone a problem directory\n"
    "    conf                setup an Idefix problem\n"
    "    read                read an Idefix inifile and print it to json format\n"
    "    run                 run an Idefix problem\n"
    "    stamp               print relevant data for reproduction to stdout\n"
    "    write               write an Idefix inifile from a json string\n"
    "\n"
    f"{OPTIONAL_SEC}:\n"
    "  -h, --help            show this help message and exit\n"
    "  -v, --version         show program's version number and exit\n"
)


def test_no_command_passed(capsys):
    ret = main([])
    assume(ret != 0)
    out, err = capsys.readouterr()
    assume(out == "")
    # skip the first lines because they differ between macos and linux
    assert err.splitlines()[2:] == HELP_MESSAGE.splitlines()[2:]
