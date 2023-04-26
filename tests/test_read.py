import json

from pytest_check import check

from idefix_cli.__main__ import main


def test_read_not_a_file(tmp_path, capsys):
    target = tmp_path / "not_a_file"
    ret = main(["read", str(target.absolute())])
    with check:
        assert ret != 0

    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert err == f"💥 no such file {target.absolute()}\n"


def test_read(inifile, capsys):
    ret = main(["read", str(inifile.absolute())])
    with check:
        assert ret == 0

    out, err = capsys.readouterr()

    # json validation
    json.loads(out)
    with check:
        assert err == ""
