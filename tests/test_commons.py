import os
import sys

from pytest import assume

from idefix_cli._commons import requires_idefix


@requires_idefix()
def noop() -> int:
    """A fake command"""
    print("hello stdout")
    print("hello stderr", file=sys.stderr)
    return 0


def test_requires_idefix_undef(capsys, monkeypatch):
    monkeypatch.delenv("IDEFIX_DIR", raising=False)
    ret = noop()
    assume(ret == 10)

    out, err = capsys.readouterr()
    assume(out == "")
    assume(err == "💥 this functionality requires $IDEFIX_DIR to be defined\n")


def test_requires_idefix_not_a_directory(capsys, monkeypatch, tmp_path):
    tmp_idefix_dir = str(tmp_path / "idefix")
    monkeypatch.setenv("IDEFIX_DIR", tmp_idefix_dir)
    ret = noop()
    assume(ret == 20)

    out, err = capsys.readouterr()
    assume(out == "")
    assume(
        err.replace("\n", "")
        == (
            "💥 env variable $IDEFIX_DIR isn't properly defined: "
            f"{tmp_idefix_dir} is not a directory"
        )
    )


def test_requires_idefix_def(capsys, monkeypatch, tmp_path):
    tmp_idefix_dir = str(tmp_path / "idefix")
    os.mkdir(tmp_idefix_dir)
    monkeypatch.setenv("IDEFIX_DIR", tmp_idefix_dir)

    ret = noop()
    assume(ret == 0)

    out, err = capsys.readouterr()
    assume(out == "hello stdout\n")
    assume(err == "hello stderr\n")
