import json
import re
import sys
from pathlib import Path

from idefix_cli.__main__ import main
from idefix_cli._commands.digest import command as digest

if sys.version_info >= (3, 11):
    from contextlib import chdir
else:
    from idefix_cli.lib import chdir
DATADIR = Path(__file__).parent / "data"
BASE_SETUP = DATADIR / "OrszagTang3D"


def test_digest_in_situ(capsys):
    with chdir(BASE_SETUP):
        ret = main(["digest"])
    out, err = capsys.readouterr()
    assert ret == 0
    json.loads(out)  # validate output
    assert err == ""


def test_digest_dir(capsys):
    ret = main(["digest", "--dir", str(BASE_SETUP.absolute())])
    out, err = capsys.readouterr()
    assert ret == 0
    json.loads(out)  # validate output
    assert err == ""


def test_timer(capsys):
    with chdir(BASE_SETUP):
        ret = main(["digest", "--timeit"])
    out, err = capsys.readouterr()
    assert ret == 0
    json.loads(out)  # validate output

    assert re.fullmatch(r"took \d+\.\d\d\d ms\n", err)


def test_invalid_dir(tmp_path, capsys):
    path = str((tmp_path / "nope").resolve())
    ret = main(["digest", "--dir", path])
    out, err = capsys.readouterr()
    assert ret != 0
    assert out == ""
    assert err == f"💥 No such directory: {path!r}\n"


def test_no_logs(tmp_path, capsys):
    path = str(tmp_path.resolve())
    ret = main(["digest", "--dir", path])
    out, err = capsys.readouterr()
    assert ret != 0
    assert out == ""
    assert err == f"💥 No log files found in {path!r}\n"


def test_failed_parsing(capsys):
    with chdir(BASE_SETUP):
        ret = digest(".", _log_line_regexp=re.compile("bad regexp"))
    out, err = capsys.readouterr()
    assert ret != 0
    assert out == ""
    assert err == "💥 Failed to parse any data\n"
