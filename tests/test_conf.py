import os

import pytest
from packaging.version import Version
from pytest import assume

from idefix_cli._commands.conf import substitute_cmake_args
from idefix_cli._main import main


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

    ret = main(["conf"])
    assume(ret != 0)

    out, err = capsys.readouterr()
    assume(out == "")
    assert f"💥 cmake is required from {usr_config.absolute()}, but " in err


@pytest.mark.parametrize(
    "args, expected",
    (
        (["-mhd"], ["-DIdefix_MHD=ON"]),
        (["--unknown-option", "1"], ["--unknown-option", "1"]),
        (["--unknown-flag", "-mhd"], ["--unknown-flag", "-DIdefix_MHD=ON"]),
        (["-mpi"], ["-DIdefix_MPI=ON"]),
        (["-arch", "Ampere86"], ["-DKokkos_ARCH_AMPERE86=ON"]),
    ),
)
@pytest.mark.usefixtures("isolated_conf_dir")
def test_cmake_subs(args, expected):
    ret = substitute_cmake_args(args)
    assert ret == expected