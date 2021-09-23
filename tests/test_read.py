import json

from pytest import assume

from idefix_cli._main import main


def test_read_not_a_file(tmp_path, capsys):
    target = tmp_path / "not_a_file"
    ret = main(["read", str(target.absolute())])
    assume(ret != 0)
    out, err = capsys.readouterr()
    assume(out == "")
    assume(err == f"ERROR no such file {target.absolute()}\n")


def test_read(inifile, capsys):
    ret = main(["read", str(inifile.absolute())])
    assume(ret == 0)

    out, err = capsys.readouterr()

    # json validation
    json.loads(out)
    assume(err == "")
