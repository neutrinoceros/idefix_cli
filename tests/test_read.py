import json

from idefix_cli.main import main


def test_read_not_a_file(tmp_path, capsys):
    target = tmp_path / "not_a_file"
    ret = main(["read", str(target.absolute())])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"ERROR no such file {target.absolute()}\n"


def test_read(inifile, capsys):
    ret = main(["read", str(inifile.absolute())])
    assert ret == 0

    out, err = capsys.readouterr()

    # json validation
    json.loads(out)
    assert err == ""
