import os
from pathlib import Path

import pytest

from idefix_cli.__main__ import main

DATADIR = Path(__file__).parent / "data"
BASE_SETUP = DATADIR / "OrszagTang3D"


def test_clone_basic(capsys, tmp_path):
    dest = str(tmp_path / "new")
    ret = main(["clone", str(BASE_SETUP), dest])

    out, err = capsys.readouterr()
    assert err == ""
    assert out.startswith("Created the following files\n")
    assert "util.py\n" in out
    assert "note.txt\n" not in out
    assert ret == 0


def test_clone_to_nested_directory(capsys, tmp_path):
    dest = str(tmp_path / "parent1" / "parent2" / "child")
    main(["clone", str(BASE_SETUP), dest])

    out, err = capsys.readouterr()
    assert err == ""
    assert out.startswith("Created the following files\n")


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
        fh.write("[idfx clone]\ninclude = *.txt")

    dest = str(tmp_path / "new") + os.path.sep
    ret = main(["clone", str(BASE_SETUP), dest, "--include", "README*"])

    out, err = capsys.readouterr()
    assert f"❗ directory {dest} will be created." in err
    assert out.startswith("Created the following files\n")
    assert "README.md\n" in out
    assert "util.py\n" in out
    assert "note.txt\n" in out
    assert ret == 0


def test_include_dir(tmp_path):
    # https://github.com/neutrinoceros/idefix_cli/issues/228
    dest1 = tmp_path / "setup_with_mydir"
    main(["clone", str(BASE_SETUP), str(dest1)])
    os.mkdir(dest1 / "mydir")
    (dest1 / "mydir" / "myfile").touch()

    dest2 = tmp_path / "final"
    ret = main(["clone", str(dest1), str(dest2), "--include", "mydir"])
    assert ret == 0

    dest3 = tmp_path / "final_shallow"
    ret = main(["clone", str(dest1), str(dest3), "--include", "mydir", "--shallow"])
    assert ret == 0


def test_exclude(capsys, tmp_path):
    dest = str(tmp_path / "new")
    ret = main(["clone", str(BASE_SETUP), dest, "--exclude", "*txt", "*.py"])

    out, err = capsys.readouterr()
    assert err == ""
    assert out.startswith("Created the following files\n")
    assert "util.py\n" not in out
    assert "note.txt\n" not in out
    assert ret == 0
