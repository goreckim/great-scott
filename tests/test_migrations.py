import argparse
from unittest.mock import patch

import pytest

from great_scott import RunException
from great_scott.migrations import (
    find_youngest_shared_migration,
    get_django_apps,
    get_migrations,
    reverse_migrations,
)


class TestFindYoungestSharedMigration:
    def test_empty_lists_returns_zero(self):
        assert find_youngest_shared_migration([], []) == "zero"

    def test_all_same_returns_last_number(self):
        list1 = ["0001_initial.py", "0002_add_field.py"]
        list2 = ["0001_initial.py", "0002_add_field.py"]
        assert find_youngest_shared_migration(list1, list2) == "0002"

    def test_diverged_returns_last_common(self):
        list1 = ["0001_initial.py", "0002_add_field.py", "0003_only_in_current.py"]
        list2 = ["0001_initial.py", "0002_add_field.py"]
        assert find_youngest_shared_migration(list1, list2) == "0002"

    def test_no_common_migrations_returns_zero(self):
        list1 = ["0001_initial.py"]
        list2 = ["0001_different.py"]
        assert find_youngest_shared_migration(list1, list2) == "zero"

    def test_destination_is_empty_returns_zero(self):
        list1 = ["0001_initial.py", "0002_add_field.py"]
        list2 = []
        assert find_youngest_shared_migration(list1, list2) == "zero"


class TestGetMigrations:
    GIT_LS_TREE_OUTPUT = (
        "myapp/migrations/__init__.py\n"
        "myapp/migrations/0001_initial.py\n"
        "myapp/migrations/0002_add_field.py\n"
        "otherapp/migrations/__init__.py\n"
        "otherapp/migrations/0001_initial.py\n"
        "notmigrations/models.py\n"
    )

    def test_parses_migrations_grouped_by_app(self):
        with patch("great_scott.migrations.run", return_value=self.GIT_LS_TREE_OUTPUT):
            result = get_migrations("main")
        assert result["myapp"] == ["0001_initial.py", "0002_add_field.py"]
        assert result["otherapp"] == ["0001_initial.py"]

    def test_ignores_init_files(self):
        with patch("great_scott.migrations.run", return_value=self.GIT_LS_TREE_OUTPUT):
            result = get_migrations("main")
        for migrations in result.values():
            assert "__init__.py" not in migrations

    def test_ignores_non_migration_files(self):
        with patch("great_scott.migrations.run", return_value=self.GIT_LS_TREE_OUTPUT):
            result = get_migrations("main")
        assert "notmigrations" not in result

    def test_handles_nested_app_path(self):
        output = "apps/nested/myapp/migrations/0001_initial.py\n"
        with patch("great_scott.migrations.run", return_value=output):
            result = get_migrations("main")
        assert "myapp" in result

    def test_exits_on_git_error(self):
        with patch("great_scott.migrations.run", side_effect=RunException("fatal")):
            with pytest.raises(SystemExit):
                get_migrations("nonexistent-branch")


class TestGetDjangoApps:
    def test_returns_apps_when_django_available(self):
        with patch("great_scott.migrations.run", return_value="app1,app2\n"):
            result = get_django_apps()
        assert result == {"app1", "app2"}

    def test_returns_empty_set_when_django_not_available(self):
        with patch("great_scott.migrations.run", side_effect=RunException("")):
            result = get_django_apps()
        assert result == set()


class TestReverseMigrations:
    def _make_args(self, dst_branch="main"):
        args = argparse.Namespace()
        args.dst_branch = dst_branch
        return args

    def test_does_nothing_when_already_on_dst_branch(self):
        with patch("great_scott.migrations.run", return_value="main\n") as mock_run:
            reverse_migrations(self._make_args("main"))
        assert mock_run.call_count == 1

    def test_calls_migrate_for_diverged_apps(self):
        current_migs = "app/migrations/0001_initial.py\napp/migrations/0002_extra.py\n"
        dest_migs = "app/migrations/0001_initial.py\n"

        def fake_run(cmd, *args):
            if "--abbrev-ref" in args:
                return "feature\n"
            if "ls-tree" in args and "feature" in args:
                return current_migs
            if "ls-tree" in args and "main" in args:
                return dest_migs
            return ""

        with patch("great_scott.migrations.run", side_effect=fake_run), patch(
            "great_scott.migrations.get_django_apps", return_value={"app"}
        ):
            reverse_migrations(self._make_args("main"))

    def test_exits_when_django_not_available(self):
        with patch("great_scott.migrations.run", return_value="feature\n"), patch(
            "great_scott.migrations.get_django_apps", return_value=set()
        ):
            with pytest.raises(SystemExit):
                reverse_migrations(self._make_args("main"))
