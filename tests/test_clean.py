import pytest

from idefix_cli.commands._clean import gpatterns, kokkos_files
from idefix_cli.main import main


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


def test_patterns():
    assert not kokkos_files.intersection(gpatterns)


@pytest.mark.parametrize("pattern", [p for p in kokkos_files if "*" in p])
def test_clean_wildcards(pattern, tmp_path):
    file_to_clean = tmp_path / pattern.replace("*", "legit_file_prefix")
    file_to_clean.touch()
    main(["clean", str(tmp_path.absolute())])
    assert not list(tmp_path.iterdir())


def test_clean_only_kokkos(dirty_tmp_dir):
    tmp_path, targets, survivors = dirty_tmp_dir

    main(["clean", str(tmp_path.absolute())])

    for name in targets:
        assert not name.is_file()
    for name in survivors:
        assert name.is_file()


def test_clean_all(messy_tmp_dir):
    tmp_path, targets, killable, survivors = messy_tmp_dir

    main(["clean", str(tmp_path.absolute()), "--all"])

    for name in targets + killable:
        assert not name.is_file()
    for name in survivors:
        assert name.is_file()


@pytest.mark.parametrize(
    "flags", [("--dry",), ("--dry-run",), ("--dry", "--all"), ("--dry-run", "--all")]
)
def test_drymode_noop(flags, clean_tmp_dir, capsys):
    tmp_path, targets, survivors = clean_tmp_dir

    ret = main(["clean", *flags, str(tmp_path.absolute())])
    assert ret == 0
    out, err = capsys.readouterr()
    assert out == "Nothing to remove.\n"
    assert err == ""


@pytest.mark.parametrize("flag", ["--dry", "--dry-run"])
def test_drymode_dirty(flag, dirty_tmp_dir, capsys):
    tmp_path, targets, survivors = dirty_tmp_dir

    ret = main(["clean", flag, str(tmp_path.absolute())])
    assert ret == 0

    out, err = capsys.readouterr()
    file_list = "\n".join([str(t) for t in sorted(targets)])
    assert out == f"The following files would be removed.\n{file_list}\n"
    assert err == ""


@pytest.mark.parametrize("flag", ["--dry", "--dry-run"])
def test_drymode_messy(flag, messy_tmp_dir, capsys):
    tmp_path, targets, killable, survivors = messy_tmp_dir

    ret = main(["clean", flag, str(tmp_path.absolute())])
    assert ret == 0

    out, err = capsys.readouterr()
    file_list = "\n".join([str(t) for t in sorted(targets)])
    assert out == f"The following files would be removed.\n{file_list}\n"
    assert err == ""


@pytest.mark.parametrize("flag", ["--dry", "--dry-run"])
def test_drymode_messy_all(flag, messy_tmp_dir, capsys):
    tmp_path, targets, killable, survivors = messy_tmp_dir

    ret = main(["clean", str(tmp_path.absolute()), flag, "--all"])
    assert ret == 0

    out, err = capsys.readouterr()
    file_list = "\n".join([str(t) for t in sorted(targets + killable)])
    assert out == f"The following files would be removed.\n{file_list}\n"
    assert err == ""
