import io
import json
import re
import subprocess

import pytest

from idefix_cli.main import main

jq_available = subprocess.run(["which", "jq"]).returncode == 0

simple_conf = {"Grid": {"x": 1, "y": 2}}
simple_conf = json.dumps(simple_conf)
simple_conf_as_ini = "[Grid]\nx 1\ny 2"


def normalise_whitespace(s):
    lines = s.splitlines()
    ret = [re.sub(r"\s+", " ", line) for line in lines]
    # remove empty lines
    ret = [line for line in ret if line]
    return "\n".join(ret)


def test_write_simple_conf(inifile, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(simple_conf))
    ret = main(["read", str(inifile.absolute())])
    assert ret == 0
    out, err = capsys.readouterr()

    target = tmp_path / "idefix.mod.ini"
    ret = main(["write", str(target.absolute())])
    assert ret == 0

    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert target.is_file()
    assert normalise_whitespace(target.read_text()) == simple_conf_as_ini


def test_write_file_exists(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(simple_conf))

    target = tmp_path / "idefix.mod.ini"
    target.touch()
    # a minimalist configuration respecting Idefix inifile format

    ret = main(["write", str(target.absolute())])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == f"ERROR destination file {target} already exists. Use -f/--force to overwrite.\n"
    )
    assert target.read_text() == ""


@pytest.mark.parametrize("flag", ["-f", "--force"])
def test_write_file_exists_force(flag, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(simple_conf))

    target = tmp_path / "idefix.mod.ini"
    target.touch()

    ret = main(["write", str(target.absolute()), flag])
    assert ret == 0

    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert target.is_file()
    assert normalise_whitespace(target.read_text()) == simple_conf_as_ini


def test_invalid_json(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("1" + simple_conf))

    target = tmp_path / "idefix.mod.ini"

    ret = main(["write", str(target.absolute())])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "ERROR input is not valid json.\n"

    # test that this is still what happens even if the target file exists
    target.touch()
    ret = main(["write", str(target.absolute())])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "ERROR input is not valid json.\n"


def test_invalid_inifile(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({1: 2})))

    target = tmp_path / "idefix.mod.ini"

    ret = main(["write", str(target.absolute())])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "ERROR input is not Pluto inifile format compliant.\n"
