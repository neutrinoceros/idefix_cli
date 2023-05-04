import os

from idefix_cli.lib import run_subcommand


def test_simple_subcommand(capsys):
    run_subcommand(["ls"])
    out, err = capsys.readouterr()
    assert out.startswith("🚀 running ls")
    assert err == ""


def test_subcommand_from_loc(capsys, tmp_path):
    run_subcommand(["ls"], loc=tmp_path)
    out, err = capsys.readouterr()
    assert out.startswith(f"🚀 running ls (from {tmp_path}{os.sep})")
    assert err == ""
