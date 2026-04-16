from __future__ import annotations

from collections import defaultdict
from itertools import takewhile
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from . import (
    Ansi,
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
                "print(','.join(apps.app_configs.keys()))",
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

    app_to_migrations: defaultdict[str, list[str]] = defaultdict(list)
    for path in files:
        p = PurePosixPath(path)
        if p.parent.name != "migrations" or p.name == "__init__.py":
            continue
        app_to_migrations[p.parent.parent.name].append(p.name)

    return app_to_migrations


def find_youngest_shared_migration(list1: list[str], list2: list[str]) -> str:
    common = list(takewhile(lambda pair: pair[0] == pair[1], zip(list1, list2)))
    if not common:
        return "zero"
    return common[-1][0].split("_", 1)[0]


def reverse_migrations(args: argparse.Namespace) -> None:
    if not django_available():
        fail("Django not found, won't reverse any migrations 🤷")

    try:
        current_branch = run("git", "rev-parse", "--abbrev-ref", "HEAD").strip()
    except RunException as ex:
        fail(str(ex))

    if current_branch == args.dst_branch:
        return

    info("Getting a list of Django applications...")
    available_apps = get_django_apps()

    all_current_migrations = get_migrations(current_branch)
    all_dest_migrations = get_migrations(args.dst_branch)

    info(
        f"👀 Looking for migrations to reverse on "
        f"{Ansi.UNDERLINE}{current_branch}{Ansi.END}...",
        delete_last_line=True,
    )
    migrations_reversed = 0
    for app, current_migrations in all_current_migrations.items():
        if app not in available_apps:
            continue

        dest_migrations = all_dest_migrations[app]
        youngest = find_youngest_shared_migration(current_migrations, dest_migrations)

        last_migration_number = current_migrations[-1].split("_", 1)[0]
        if last_migration_number == youngest:
            continue

        info(
            f"⚠️ reversing migrations for "
            f"{Ansi.BOLD}{app}{Ansi.END} (up to {youngest})"
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
