from idefix_cli.__main__ import main


def test_times_without_one_step(capsys):
    ret = main(["run", "--times", "1"])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == (
        "💥 the --times parameter is invalid if --one/--one-step isn't passed too\n"
    )


def test_negative_times(capsys):
    ret = main(["run", "--one", "--times", "-1"])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == (
        "💥 the --times parameter expects a strictly positive integer (got -1)\n"
    )


def test_one_and_maxncycles(capsys):
    ret = main(["run", "--one", "-maxcycles", "1"])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "💥 -maxcycles cannot be combined with --one/--one-step\n"
