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
    assume(err == "ERROR this functionality requires $IDEFIX_DIR to be defined.\n")


def test_requires_idefix_def(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("IDEFIX_DIR", str(tmp_path / "idefix"))

    ret = noop()
    assume(ret == 0)

    out, err = capsys.readouterr()
    assume(out == "hello stdout\n")
    assume(err == "hello stderr\n")
