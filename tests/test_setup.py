import sys

from idefix_cli._commons import print_err, print_warning
from idefix_cli.commands._setup import wrap_outputs
from idefix_cli.main import main


def test_wrap_outputs(capsys):

    stdout = b"Everything went ok"
    errors = [
        b"Error: received malformed data",
        b"Warning: something non-fatal is wrong",
        b"something else is considered err",
    ]
    stderr = b"\n".join(errors)

    res = wrap_outputs(stdout, stderr)
    out0, err0 = capsys.readouterr()
    assert res is None

    print(stdout.decode())
    print_err("received malformed data")
    print_warning("something non-fatal is wrong")
    print("something else is considered err", file=sys.stderr)
    out1, err1 = capsys.readouterr()
    assert out0 == out1
    assert err0 == err1


def test_dummy_wrapped_setup_script(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("IDEFIX_DIR", str(tmp_path))
    with open(tmp_path / "configure.py", "wt") as fh:
        fh.writelines(
            [
                "import sys\n",
                "print('Successfully configured Idefix')\n",
                "sys.exit(0)\n",
            ]
        )
    ret = main(["setup", "."])
    assert ret == 0
    out, err = capsys.readouterr()
    assert out == "Successfully configured Idefix\n\n"
    assert err == ""
