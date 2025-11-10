import json

from idefix_cli.__main__ import idfx_entry_point as main


def test_read_not_a_file(capsys, subtests, tmp_path):
    target = tmp_path / "not_a_file"
    ret = main(["read", str(target.absolute())])
    with subtests.test():
        assert ret != 0

    out, err = capsys.readouterr()
    with subtests.test():
        assert out == ""
    with subtests.test():
        assert err == f"💥 no such file {target.absolute()}\n"


def test_read(inifile, capsys, subtests):
    ret = main(["read", str(inifile.absolute())])
    with subtests.test():
        assert ret == 0

    out, err = capsys.readouterr()

    # json validation
    json.loads(out)
    with subtests.test():
        assert err == ""
