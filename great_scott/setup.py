from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from . import (
    RunException,
    fail,
    info,
    run,
)


if TYPE_CHECKING:
    import argparse


gs_pre_checkout_template = """#!/usr/bin/env bash
# this checks if HEAD is detached, 0 means normal 1 is detached
if git symbolic-ref -q HEAD > /dev/null;
then
    export GS_PRE_CHECKOUT=true
    export GS_DST_BRANCH=`git rev-parse --abbrev-ref HEAD`
    git switch --quiet -
    {script_path} reverse --dst-branch "$GS_DST_BRANCH"
    git switch --quiet -
fi
"""


post_checkout_template = """#!/usr/bin/env bash
{invoke_pre_checkout}
"""

invoke_pre_checkout = (
    'if [ -n "$GS_PRE_CHECKOUT" ] && "$GS_PRE_CHECKOUT"; '
    "then exit 0; "
    "else . .git/hooks/gs-pre-checkout; fi"
)

python_path = sys.executable
script_path = Path(python_path).with_name("great-scott")


def get_git_hooks_path() -> Path:
    try:
        return (
            Path(run("git", "rev-parse", "--show-toplevel").strip()) / ".git" / "hooks"
        )
    except RunException:
        fail(
            "fatal: not a git repository (or any of the parent directories), "
            "quitting..."
        )


def _install_post_checkout(git_hooks_path: Path) -> None:
    """Install post-checkout script"""
    post_checkout_path = git_hooks_path / "post-checkout"
    if not post_checkout_path.exists():
        with open(post_checkout_path, "w") as f:
            f.write(
                post_checkout_template.format(invoke_pre_checkout=invoke_pre_checkout)
            )
        post_checkout_path.chmod(0o755)
        return

    with open(post_checkout_path) as f:
        post_checkout_script_lines = list(map(lambda s: s.strip(), f.readlines()))

    if (
        not post_checkout_script_lines[0].startswith("#!")
        or "/bin/sh" not in post_checkout_script_lines[0]
        and "bash" not in post_checkout_script_lines[0]
    ):
        fail("post-checkout is not a bash or a sh script, quitting...")

    if invoke_pre_checkout in post_checkout_script_lines:
        # call is already in the script
        return

    post_checkout_script_lines.insert(1, invoke_pre_checkout)
    with open(post_checkout_path, "w") as f:
        f.write("\n".join(post_checkout_script_lines) + "\n")


def _uninstall_post_checkout(git_hooks_path: Path) -> None:
    """Remove call to pre-checkout from post-checkout script"""
    post_checkout_path = git_hooks_path / "post-checkout"
    if not post_checkout_path.exists():
        return

    with open(post_checkout_path) as f:
        post_checkout_script_lines = list(map(lambda s: s.strip(), f.readlines()))

    try:
        post_checkout_script_lines.remove(invoke_pre_checkout)
    except ValueError:
        return

    with open(post_checkout_path, "w") as f:
        f.write("\n".join(post_checkout_script_lines) + "\n")


def _install_pre_checkout(git_hooks_path: Path) -> None:
    """Install pre-checkout script"""
    pre_checkout_path = git_hooks_path / "gs-pre-checkout"
    with open(pre_checkout_path, "w") as f:
        f.write(
            gs_pre_checkout_template.format(
                script_path=script_path,
            )
        )
    pre_checkout_path.chmod(0o755)


def _uninstall_pre_checkout(git_hooks_path: Path) -> None:
    """Remove gs-pre-checkout script"""
    pre_checkout_path = git_hooks_path / "gs-pre-checkout"
    if pre_checkout_path.exists():
        pre_checkout_path.unlink()


def install(args: argparse.Namespace) -> None:
    info("Installing git hooks...")
    if not script_path.exists():
        fail(f"{script_path} script does not exist, quitting...")

    git_hooks_path = get_git_hooks_path()

    _install_post_checkout(git_hooks_path)
    _install_pre_checkout(git_hooks_path)

    info("git hooks installed!", delete_last_line=True)


def uninstall(args: argparse.Namespace) -> None:
    info("Uninstalling git hooks...")
    git_hooks_path = get_git_hooks_path()

    _uninstall_post_checkout(git_hooks_path)
    _uninstall_pre_checkout(git_hooks_path)

    info("git hooks uninstalled!", delete_last_line=True)
