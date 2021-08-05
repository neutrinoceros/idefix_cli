from pytest import assume

from idefix_cli.main import main

HELP_MESSAGE = """usage: idfx [-h] [-v] {clean,clone,read,run,setup,stamp,write} ...

positional arguments:
  {clean,clone,read,run,setup,stamp,write}
    clean               clean up generated files
    clone               clone a problem directory
    read                read an Idefix inifile and print it to json format
    run                 run an Idefix problem
    setup               setup an Idefix problem
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
    assume(err.splitlines()[2:] == HELP_MESSAGE.splitlines()[2:])
