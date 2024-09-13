from __future__ import annotations

import importlib.metadata
import subprocess
import sys
from typing import NoReturn


__version__ = importlib.metadata.version("great-scott")


class RunException(Exception):
    pass


class TEXT:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def run(command: str, *args: str) -> str | None:
    sp = subprocess.run([command, *args], capture_output=True, text=True)
    if sp.returncode != 0:
        raise RunException(sp.stderr)
    return sp.stdout


def fail(msg: str, status: int = 1) -> NoReturn:
    print(f"☠️ {msg}")
    exit(status)


def info(msg: str, delete_last_line: bool = False) -> None:
    if delete_last_line:
        sys.stdout.write("\x1b[1A\x1b[2K")
    print(f"{msg}")
