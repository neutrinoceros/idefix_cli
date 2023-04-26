from idefix_cli.__main__ import main


def test_times_without_one_step(capsys):
    ret = main(["run", "--times", "1"])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "💥 --times argument is invalid if --one/--one-step isn't passed too\n"
