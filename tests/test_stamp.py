import json
from dataclasses import dataclass
from getpass import getuser
from socket import gethostname
from typing import Tuple

import pytest
from pytest_check import check

from idefix_cli._main import main

mock_data = {
    "latest ancestor version": "unknown version",
    "sha": "864e17a23eebbccMOCKSHA1e3db466325d54b51a",
    "user": getuser(),
    "host": gethostname(),
}


@dataclass(frozen=True)
class MockObject:
    hexsha: str = mock_data["sha"]


@dataclass(frozen=True)
class MockHead:
    object: MockObject = MockObject()


@dataclass
class MockRepo:
    # I'm adding a meaningless "slot" attr here because pytest silently replaces my first attribute
    # with the test id. This is likely a bug on their side but for now I'll just work around it.
    slot: str
    head: MockHead = MockHead()
    tags: Tuple[str] = (mock_data["latest ancestor version"],)


@pytest.mark.parametrize("flag", ["", "-d", "--json"])
def test_stamp_no_idefix(flag, capsys, monkeypatch):
    monkeypatch.delenv("IDEFIX_DIR", raising=False)

    argv = ["stamp"]
    if flag:
        argv.append(flag)

    ret = main(argv)
    with check:
        assert ret == 10

    out, err = capsys.readouterr()
    with check:
        assert out == ""
    with check:
        assert err == "💥 this functionality requires $IDEFIX_DIR to be defined\n"


def test_stamp_simple(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("IDEFIX_DIR", str(tmp_path))
    monkeypatch.setattr("git.Repo", MockRepo)

    ret = main(["stamp"])
    with check:
        assert ret == 0
    out, err = capsys.readouterr()
    # skiping the last line as it contains a date and I'm not sure how to test it.
    with check:
        assert out.splitlines()[:-1] == [v for v in mock_data.values()]
    with check:
        assert err == ""


@pytest.mark.parametrize("flag", ["-d", "--json"])
def test_stamp_json(flag, capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("IDEFIX_DIR", str(tmp_path))
    monkeypatch.setattr("git.Repo", MockRepo)

    ret = main(["stamp", flag])
    with check:
        assert ret == 0
    out, err = capsys.readouterr()
    # json validataion
    json.loads(out)
    with check:
        assert err == ""
