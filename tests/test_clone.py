import os
from pathlib import Path

import pytest

from idefix_cli._main import main

DATADIR = Path(__file__).parent / "data"
BASE_SETUP = DATADIR / "OrszagTang3D"


def test_clone_basic(capsys, tmp_path):
    dest = str(tmp_path / "new")
    ret = main(["clone", str(BASE_SETUP), dest])

    out, err = capsys.readouterr()
    assert err == ""
    assert out.startswith("Created the following files\n")
    assert ret == 0


def test_clone_with_terminal_sep(capsys, tmp_path):
    # see https://github.com/neutrinoceros/idefix_cli/issues/116
    dest = str(tmp_path / "new") + os.path.sep
    ret = main(["clone", str(BASE_SETUP), dest])

    out, err = capsys.readouterr()
    assert err.startswith(f"❗ directory {dest} will be created.")
    assert out.startswith("Created the following files\n")
    assert ret == 0


def test_include_from_conf(capsys, tmp_path, isolated_conf_dir):
    with open(isolated_conf_dir / "idefix.cfg", "w") as fh:
        fh.write("[idfx clone]\ninclude = README*")

    dest = str(tmp_path / "new") + os.path.sep
    ret = main(["clone", str(BASE_SETUP), dest])

    out, err = capsys.readouterr()
    assert f"❗ directory {dest} will be created." in err
    assert out.startswith("Created the following files\n")
    assert "README.md\n" in out
    assert ret == 0


@pytest.mark.usefixtures("isolated_conf_dir")
def test_include_from_cli(capsys, tmp_path):
    dest = str(tmp_path / "new") + os.path.sep
    ret = main(["clone", str(BASE_SETUP), dest, "--include", "README*"])

    out, err = capsys.readouterr()
    assert f"❗ directory {dest} will be created." in err
    assert out.startswith("Created the following files\n")
    assert "README.md\n" in out
    assert ret == 0


def test_include_from_conf_and_cli(capsys, tmp_path, isolated_conf_dir):
    with open(isolated_conf_dir / "idefix.cfg", "w") as fh:
        fh.write("[idfx clone]\ninclude = *.py")

    dest = str(tmp_path / "new") + os.path.sep
    ret = main(["clone", str(BASE_SETUP), dest, "--include", "README*"])

    out, err = capsys.readouterr()
    assert f"❗ directory {dest} will be created." in err
    assert out.startswith("Created the following files\n")
    assert "README.md\n" in out
    assert "util.py\n" in out
    assert ret == 0
