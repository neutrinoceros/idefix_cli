import pytest

from idefix_cli.commands._clean import gpatterns, kokkos_files
from idefix_cli.main import main


def replace_wildcards(names):
    return [name.replace("*", "a") for name in names]


def test_patterns():
    assert not kokkos_files.intersection(gpatterns)


@pytest.mark.parametrize("pattern", [p for p in kokkos_files if "*" in p])
def test_clean_wildcards(pattern, tmp_path):
    file_to_clean = tmp_path / pattern.replace("*", "legit_file_prefix")
    file_to_clean.touch()
    main(["clean", str(tmp_path.absolute())])
    assert not list(tmp_path.iterdir())


def test_clean_only_kokkos(tmp_path):
    for name in replace_wildcards(kokkos_files.union(gpatterns)):
        (tmp_path / name).touch()

    main(["clean", str(tmp_path.absolute())])

    for name in replace_wildcards(kokkos_files):
        assert not (tmp_path / name).is_file()
    for name in replace_wildcards(gpatterns):
        assert (tmp_path / name).is_file()


def test_clean_all(tmp_path):
    targets = replace_wildcards(kokkos_files.union(gpatterns))
    survivors = ["setup.py", "README.md", "idefix.ini", "pluto.ini"]

    for name in targets + survivors:
        (tmp_path / name).touch()

    main(["clean", str(tmp_path.absolute()), "--all"])

    for name in targets:
        assert not (tmp_path / name).is_file()
    for name in survivors:
        assert (tmp_path / name).is_file()
