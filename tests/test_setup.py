import pytest

from great_scott.setup import (
    _install_post_checkout,
    _install_pre_checkout,
    _uninstall_post_checkout,
    _uninstall_pre_checkout,
    invoke_pre_checkout,
)


class TestInstallPostCheckout:
    def test_creates_file_when_not_exists(self, tmp_path):
        _install_post_checkout(tmp_path)
        assert (tmp_path / "post-checkout").exists()

    def test_created_file_is_executable(self, tmp_path):
        _install_post_checkout(tmp_path)
        mode = (tmp_path / "post-checkout").stat().st_mode
        assert mode & 0o111

    def test_appends_invocation_to_existing_bash_script(self, tmp_path):
        existing = tmp_path / "post-checkout"
        existing.write_text("#!/bin/bash\necho done\n")
        _install_post_checkout(tmp_path)
        content = existing.read_text()
        assert invoke_pre_checkout in content

    def test_does_not_duplicate_invocation(self, tmp_path):
        existing = tmp_path / "post-checkout"
        existing.write_text(f"#!/bin/bash\n{invoke_pre_checkout}\n")
        _install_post_checkout(tmp_path)
        content = existing.read_text()
        assert content.count(invoke_pre_checkout) == 1

    def test_exits_on_non_bash_script(self, tmp_path):
        existing = tmp_path / "post-checkout"
        existing.write_text("#!/usr/bin/env python\nprint('hi')\n")
        with pytest.raises(SystemExit):
            _install_post_checkout(tmp_path)


class TestUninstallPostCheckout:
    def test_removes_invocation_line(self, tmp_path):
        existing = tmp_path / "post-checkout"
        existing.write_text(f"#!/bin/bash\n{invoke_pre_checkout}\necho done\n")
        _uninstall_post_checkout(tmp_path)
        assert invoke_pre_checkout not in existing.read_text()

    def test_noop_when_file_does_not_exist(self, tmp_path):
        _uninstall_post_checkout(tmp_path)  # should not raise

    def test_noop_when_invocation_not_present(self, tmp_path):
        existing = tmp_path / "post-checkout"
        existing.write_text("#!/bin/bash\necho done\n")
        original = existing.read_text()
        _uninstall_post_checkout(tmp_path)
        assert existing.read_text() == original


class TestInstallPreCheckout:
    def test_creates_gs_pre_checkout_file(self, tmp_path):
        _install_pre_checkout(tmp_path)
        assert (tmp_path / "gs-pre-checkout").exists()

    def test_file_is_executable(self, tmp_path):
        _install_pre_checkout(tmp_path)
        mode = (tmp_path / "gs-pre-checkout").stat().st_mode
        assert mode & 0o111

    def test_file_contains_reverse_command(self, tmp_path):
        _install_pre_checkout(tmp_path)
        content = (tmp_path / "gs-pre-checkout").read_text()
        assert "great-scott" in content
        assert "reverse" in content


class TestUninstallPreCheckout:
    def test_removes_gs_pre_checkout(self, tmp_path):
        hook = tmp_path / "gs-pre-checkout"
        hook.write_text("#!/bin/bash\n")
        _uninstall_pre_checkout(tmp_path)
        assert not hook.exists()

    def test_noop_when_file_does_not_exist(self, tmp_path):
        _uninstall_pre_checkout(tmp_path)  # should not raise
