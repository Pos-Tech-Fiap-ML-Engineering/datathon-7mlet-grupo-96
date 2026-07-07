import pytest

from bandit_platform import __version__
from bandit_platform.cli import main


def test_version_flag_exits_zero_and_prints_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_no_args_returns_zero():
    assert main([]) == 0
