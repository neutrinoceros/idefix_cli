import io
import json
import re
import subprocess

import pytest
from pytest_check import check

from idefix_cli.__main__ import main

jq_available = subprocess.run(["which", "jq"]).returncode == 0

data = {"Grid": {"x": 1, "y": 2}}
simple_conf = json.dumps(data)
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
    with check:
        assert ret == 0
    out, err = capsys.readouterr()

    target = tmp_path / "idefix.mod.ini"
    ret = main(["write", str(target.absolute())])
    with check:
        assert ret == 0

    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert err == ""
    with check:
        assert target.is_file()
    with check:
        assert normalise_whitespace(target.read_text()) == simple_conf_as_ini


def test_write_file_exists(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(simple_conf))

    target = tmp_path / "idefix.mod.ini"
    target.touch()
    # a minimalist configuration respecting Idefix inifile format

    ret = main(["write", str(target.absolute())])
    with check:
        assert ret != 0
    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert (
            err
            == f"💥 destination file {target} already exists. Use -f/--force to overwrite.\n"
        )
    with check:
        assert target.read_text() == ""


@pytest.mark.parametrize("flag", ["-f", "--force"])
def test_write_file_exists_force(flag, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(simple_conf))

    target = tmp_path / "idefix.mod.ini"
    target.touch()

    ret = main(["write", str(target.absolute()), flag])
    with check:
        assert ret == 0

    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert err == ""
    with check:
        assert target.is_file()
    with check:
        assert normalise_whitespace(target.read_text()) == simple_conf_as_ini


def test_invalid_json(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("1" + simple_conf))

    target = tmp_path / "idefix.mod.ini"

    ret = main(["write", str(target.absolute())])
    with check:
        assert ret != 0
    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert err == "💥 input is not valid json.\n"

    # test that this is still what happens even if the target file exists
    target.touch()
    ret = main(["write", str(target.absolute())])
    with check:
        assert ret != 0
    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert err == "💥 input is not valid json.\n"


def test_invalid_inifile(capsys, tmp_path, monkeypatch):
    invalid_json = json.dumps({"section": {"subsection": {"subsubsection": 2}}})
    monkeypatch.setattr("sys.stdin", io.StringIO(invalid_json))

    target = tmp_path / "idefix.mod.ini"

    ret = main(["write", str(target.absolute())])
    with check:
        assert ret != 0
    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert err == "💥 input is not Pluto inifile format compliant.\n"
