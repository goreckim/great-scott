from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from . import (
    TEXT,
    RunException,
    fail,
    info,
    run,
)


if TYPE_CHECKING:
    import argparse


def django_available() -> bool:
    try:
        run("python", "-m", "django", "--version")
    except RunException:
        return False
    return True


def get_django_apps() -> set[str]:
    try:
        return set(
            run(
                "python",
                "manage.py",
                "shell",
                "-c",
                "from django.apps import apps; "
                "print(','.join(list(apps.app_configs.keys())))",
            )
            .strip()
            .split(",")
        )
    except RunException as ex:
        fail(str(ex))


def get_migrations(branch: str) -> defaultdict[str, list[str]]:
    try:
        files = sorted(run("git", "ls-tree", "-r", "--name-only", branch).split())
    except RunException as ex:
        fail(str(ex))

    app_to_migrations = defaultdict(list)
    for path in files:
        if "/migrations/" not in path:
            continue
        app, migration = path.split("/migrations/")
        app = app.split("/")[-1]
        if migration == "__init__.py":
            continue
        app_to_migrations[app].append(migration)

    return app_to_migrations


def find_youngest_shared_migration(list1: list[str], list2: list[str]) -> str:
    youngest = "zero"
    for migration1, migration2 in zip(list1, list2):
        if migration1 != migration2:
            break
        youngest = migration1.split("_", 1)[0]
    return youngest


def reverse_migrations(args: argparse.Namespace) -> None:
    if not django_available():
        fail("Django not found, won't reverse any migrations 🤷")

    try:
        current_branch = run("git", "rev-parse", "--abbrev-ref", "HEAD").strip()
    except RunException as ex:
        fail(str(ex))

    if current_branch == args.dst_branch:
        # no need to reverse if the current branch is the destination branch
        return

    info("Getting a list of Django applications...")
    available_apps = get_django_apps()

    all_current_migrations = get_migrations(current_branch)
    all_dest_migrations = get_migrations(args.dst_branch)

    info(
        f"👀 Looking for migrations to reverse on "
        f"{TEXT.UNDERLINE}{current_branch}{TEXT.END}...",
        delete_last_line=True,
    )
    migrations_reversed = 0
    for app, current_migrations in all_current_migrations.items():
        if app not in available_apps:
            # additional check against migration files for an application not
            # registered in the project.
            continue

        dest_migrations = all_dest_migrations[app]
        youngest = find_youngest_shared_migration(current_migrations, dest_migrations)

        if current_migrations[-1].startswith(youngest):
            # for a given application the last migration is the same on both branches,
            # there is no need to perform expensive reversals
            continue

        info(
            f"⚠️ reversing migrations for {TEXT.BOLD}{app}{TEXT.END} (up to {youngest})"
        )
        try:
            run("python", "manage.py", "migrate", app, youngest)
        except RunException as ex:
            fail(str(ex))

        migrations_reversed += 1

    if migrations_reversed:
        info(
            f"I have reversed migrations for {migrations_reversed} "
            f"app{'s' if migrations_reversed > 1 else ''}!"
        )

    else:
        info("Great Scott! No migrations to reverse!", delete_last_line=True)
