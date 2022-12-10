import os
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
INIFILES = list(DATA_DIR.glob("*.ini"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES]


@pytest.fixture(params=INIFILES, ids=INIFILES_IDS)
def inifile(request):
    return request.param


@pytest.fixture()
def isolated_conf_dir(tmp_path, monkeypatch):
    conf_dir = tmp_path / ".config"
    os.makedirs(conf_dir)
    monkeypatch.setattr("idefix_cli.lib.XDG_CONFIG_HOME", str(conf_dir))
    monkeypatch.chdir(tmp_path)
    return conf_dir
