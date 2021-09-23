import os

import pytest
from packaging.version import Version
from pytest import assume

from idefix_cli._commands.conf import has_cmake_preference
from idefix_cli._commands.conf import is_cmake_required
from idefix_cli._commands.conf import substitute_cmake_args
from idefix_cli._commons import get_user_config_file
from idefix_cli._main import main


@pytest.mark.parametrize("mode", ["local", "global"])
def test_require_cmake(mode, tmp_path, monkeypatch):
    conf_dir = tmp_path / ".config"
    os.makedirs(conf_dir)
    monkeypatch.setattr("idefix_cli._commons.XDG_CONFIG_HOME", str(conf_dir))

    monkeypatch.chdir(tmp_path)
    assert get_user_config_file() is None
    assert has_cmake_preference()
    assert not is_cmake_required()

    cfg = {"local": "idefix.cfg", "global": str(conf_dir / "idefix.cfg")}[mode]
    with open(cfg, "w") as fh:
        fh.write("[some valid section]\nparam=value\n")

    assert not is_cmake_required()

    with open(cfg, "a") as fh:
        fh.write("[idefix_cli]\nconf_system=cmake\n")
    assert is_cmake_required()
    assert has_cmake_preference()

    with open(cfg, "a") as fh:
        fh.write("[compilation]\nCPU=BDW\n")

    assert is_cmake_required()
    assert not has_cmake_preference()


def test_setup_requiring_cmake_in_bad_env(capsys, tmp_path, monkeypatch):
    tmp_idefix_dir = tmp_path / "idefix"
    os.makedirs(tmp_idefix_dir / ".git")
    monkeypatch.setenv("IDEFIX_DIR", str(tmp_idefix_dir))

    monkeypatch.chdir(tmp_path)
    usr_config = tmp_path / "idefix.cfg"
    with open(usr_config, "w") as fh:
        fh.write("[idefix_cli]\nconf_system=cmake\n")

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
    assert f"ERROR cmake is required from {usr_config.absolute()}, but " in err


def test_cmake_subs():
    ret = substitute_cmake_args("-mhd", "--random", "1", "-mpi")
    assert ret == ("-DIdefix_MHD=ON", "--random", "1", "-DIdefix_MPI=ON")
