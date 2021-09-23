from pytest import assume

from idefix_cli._main import main

HELP_MESSAGE = """usage: idfx [-h] [-v] {clean,clone,conf,read,run,stamp,write} ...

positional arguments:
  {clean,clone,conf,read,run,stamp,write}
    clean               clean up generated files
    clone               clone a problem directory
    conf                setup an Idefix problem
    read                read an Idefix inifile and print it to json format
    run                 run an Idefix problem
    stamp               print relevant data for reproduction to stdout
    write               write an Idefix inifile a from json string

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
"""


def test_no_command_passed(capsys):
    ret = main([])
    assume(ret != 0)
    out, err = capsys.readouterr()
    assume(out == "")
    # skip the first lines because they differ between macos and linux
    assert err.splitlines()[2:] == HELP_MESSAGE.splitlines()[2:]
