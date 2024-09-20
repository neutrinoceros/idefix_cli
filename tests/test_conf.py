import os

import pytest
from packaging.version import Version
from pytest_check import check

from idefix_cli.__main__ import main
from idefix_cli._commands.conf import substitute_cmake_args


def test_conf_without_setup_cpp(capsys, tmp_path, monkeypatch):
    tmp_idefix_dir = tmp_path / "idefix"
    os.makedirs(tmp_idefix_dir / ".git")
    monkeypatch.setenv("IDEFIX_DIR", str(tmp_idefix_dir))

    monkeypatch.chdir(tmp_path)
    ret = main(["conf"])
    with check:
        assert ret != 0

    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert "💥 Cannot configure a directory that doesn't contain a setup.cpp" in err


def test_setup_requiring_cmake_in_bad_env(capsys, tmp_path, monkeypatch):
    tmp_idefix_dir = tmp_path / "idefix"
    os.makedirs(tmp_idefix_dir / ".git")
    monkeypatch.setenv("IDEFIX_DIR", str(tmp_idefix_dir))

    monkeypatch.chdir(tmp_path)
    usr_config = tmp_path / "idefix.cfg"
    with open(usr_config, "w") as fh:
        fh.write("[idfx conf]\nengine=cmake\n")

    # not going to test every possible case, but we want to make sure that
    # the requirements are not met for this test, so we mock (almost)
    # impossible conditions.
    mock_requirements = {"cmake": Version("9001.0.1"), "idefix": Version("9001.0.1")}
    monkeypatch.setattr(
        "idefix_cli._commands.conf.CMAKE_MIN_VERSIONS", mock_requirements
    )
    (tmp_path / "setup.cpp").touch()

    ret = main(["conf"])
    with check:
        assert ret != 0

    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert f"💥 cmake is required from {usr_config.absolute()}, but " in err


@pytest.mark.parametrize(
    "args, expected",
    (
        (["-mhd"], ["-DIdefix_MHD=ON"]),
        (["--unknown-option", "1"], ["--unknown-option", "1"]),
        (["--unknown-flag", "-mhd"], ["--unknown-flag", "-DIdefix_MHD=ON"]),
        (["-mpi"], ["-DIdefix_MPI=ON"]),
        (["-debug"], ["-DIdefix_DEBUG=ON"]),
        (["-arch", "Ampere86"], ["-DKokkos_ARCH_AMPERE86=ON"]),
    ),
)
@pytest.mark.usefixtures("isolated_conf_dir")
def test_cmake_subs(args, expected):
    ret = substitute_cmake_args(args)
    assert ret == expected
