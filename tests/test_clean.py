from io import StringIO

import pytest

from idefix_cli.__main__ import main
from idefix_cli._commands.clean import gpatterns, kokkos_files


def replace_wildcards(names):
    return [name.replace("*", "a") for name in names]


@pytest.fixture()
def clean_tmp_dir(tmp_path):
    targets = []
    survivors = [
        tmp_path / name for name in ("setup.py", "README.md", "idefix.ini", "pluto.ini")
    ]

    for name in survivors:
        name.touch()

    return tmp_path, targets, survivors


@pytest.fixture()
def dirty_tmp_dir(clean_tmp_dir):
    tmp_path, _, survivors = clean_tmp_dir
    targets = [tmp_path / name for name in replace_wildcards(kokkos_files)]

    for name in targets:
        name.touch()

    return tmp_path, targets, survivors


@pytest.fixture()
def messy_tmp_dir(dirty_tmp_dir):
    tmp_path, targets, survivors = dirty_tmp_dir
    killable = [tmp_path / name for name in replace_wildcards(gpatterns)]

    for name in killable:
        name.touch()

    return tmp_path, targets, killable, survivors


YESES = ("y\n", "Y\n", "No\ny\n", "0\n1\nyes\nY\n")
NOES = ("n\n", "N\n", "No\nn\n", "0\n1\nyes\nN\n")
VALID_USER_INPUTS = YESES + NOES
assert not set(NOES).intersection(set(YESES))


def test_patterns():
    assert not kokkos_files.intersection(gpatterns)


@pytest.mark.parametrize("pattern", [p for p in kokkos_files if "*" in p])
def test_clean_no_confirmation(pattern, capsys, tmp_path):
    file_to_clean = tmp_path / pattern.replace("*", "legit_file_prefix")
    file_to_clean.touch()

    ret = main(["clean", "--dir", str(tmp_path.absolute()), "--no-confirm"])
    assert ret == 0
    _out, err = capsys.readouterr()
    assert err == ""
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("usr_input", VALID_USER_INPUTS)
@pytest.mark.parametrize("pattern", [p for p in kokkos_files if "*" in p])
def test_clean_wildcards(pattern, usr_input, monkeypatch, tmp_path):
    file_to_clean = tmp_path / pattern.replace("*", "legit_file_prefix")
    file_to_clean.touch()

    monkeypatch.setattr("sys.stdin", StringIO(usr_input))
    main(["clean", "--dir", str(tmp_path.absolute())])

    if usr_input in YESES:
        assert not list(tmp_path.iterdir())
    else:
        assert file_to_clean.is_file()


@pytest.mark.parametrize("usr_input", VALID_USER_INPUTS)
def test_clean_only_kokkos(usr_input, dirty_tmp_dir, monkeypatch):
    tmp_path, targets, survivors = dirty_tmp_dir

    if usr_input in NOES:
        targets, survivors = (), targets + survivors

    monkeypatch.setattr("sys.stdin", StringIO(usr_input))
    main(["clean", "--dir", str(tmp_path.absolute())])

    for name in targets:
        assert not name.is_file()
    for name in survivors:
        assert name.is_file()


@pytest.mark.parametrize("usr_input", VALID_USER_INPUTS)
def test_clean_all(usr_input, messy_tmp_dir, monkeypatch):
    tmp_path, targets, killable, survivors = messy_tmp_dir

    if usr_input in YESES:
        targets = targets + killable
    else:
        targets, survivors = (), targets + killable + survivors

    monkeypatch.setattr("sys.stdin", StringIO(usr_input))
    main(["clean", "--dir", str(tmp_path.absolute()), "--all"])

    for name in targets:
        assert not name.is_file()
    for name in survivors:
        assert name.is_file()


@pytest.mark.parametrize(
    "flags", [("--dry",), ("--dry-run",), ("--dry", "--all"), ("--dry-run", "--all")]
)
def test_drymode_noop(flags, clean_tmp_dir, capsys):
    tmp_path, targets, survivors = clean_tmp_dir

    ret = main(["clean", *flags, "--dir", str(tmp_path.absolute())])
    assert ret == 0
    out, err = capsys.readouterr()
    assert out == "Nothing to remove.\n"
    assert err == ""


@pytest.mark.parametrize("flag", ["--dry", "--dry-run"])
def test_drymode_dirty(flag, dirty_tmp_dir, capsys):
    tmp_path, targets, survivors = dirty_tmp_dir

    ret = main(["clean", flag, "--dir", str(tmp_path.absolute())])
    assert ret == 0

    out, err = capsys.readouterr()
    assert out.startswith("The following files and directories can be removed\n")
    for t in targets:
        assert str(t.relative_to(tmp_path)) in out
    assert err == ""


@pytest.mark.parametrize("flag", ["--dry", "--dry-run"])
def test_drymode_messy(flag, messy_tmp_dir, capsys):
    tmp_path, targets, killable, survivors = messy_tmp_dir

    ret = main(["clean", flag, "--dir", str(tmp_path.absolute())])
    assert ret == 0

    out, err = capsys.readouterr()
    assert out.startswith("The following files and directories can be removed\n")
    for t in targets:
        assert str(t.relative_to(tmp_path)) in out
    assert err == ""


@pytest.mark.parametrize("flag", ["--dry", "--dry-run"])
def test_drymode_messy_all(flag, messy_tmp_dir, capsys):
    tmp_path, targets, killable, survivors = messy_tmp_dir

    ret = main(["clean", "--dir", str(tmp_path.absolute()), flag, "--all"])
    assert ret == 0

    out, err = capsys.readouterr()
    assert out.startswith("The following files and directories can be removed\n")
    for t in targets + killable:
        assert str(t.relative_to(tmp_path)) in out
    assert err == ""
