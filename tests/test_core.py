import pytest

from great_scott import (
    RunException,
    fail,
    info,
    run,
)


class TestRun:
    def test_returns_stdout_on_success(self):
        result = run("echo", "hello")
        assert result == "hello\n"

    def test_raises_on_nonzero_exit(self):
        with pytest.raises(RunException):
            run("false")

    def test_stderr_is_in_exception_message(self):
        with pytest.raises(RunException, match="No such file or directory"):
            run("ls", "/nonexistent_path_xyz")


class TestFail:
    def test_exits_with_default_status_1(self):
        with pytest.raises(SystemExit) as exc_info:
            fail("boom")
        assert exc_info.value.code == 1

    def test_exits_with_custom_status(self):
        with pytest.raises(SystemExit) as exc_info:
            fail("boom", status=42)
        assert exc_info.value.code == 42

    def test_prints_message(self, capsys):
        with pytest.raises(SystemExit):
            fail("something went wrong")
        assert "something went wrong" in capsys.readouterr().out


class TestInfo:
    def test_prints_message(self, capsys):
        info("hello world")
        assert "hello world" in capsys.readouterr().out

    def test_delete_last_line_writes_escape(self, capsys):
        info("first")
        info("second", delete_last_line=True)
        out = capsys.readouterr().out
        assert "\x1b[1A\x1b[2K" in out
        assert "second" in out
