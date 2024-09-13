import argparse

from . import __version__
from .migrations import reverse_migrations
from .setup import (
    install,
    uninstall,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="great-scott",
        description="A simple tool to automatically, "
        "when changing git branches, "
        "reverse migrations in a Django application.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sp = parser.add_subparsers()

    sp_install = sp.add_parser("install", help="Installs git hooks")
    sp_install.set_defaults(func=install)

    sp_uninstall = sp.add_parser("uninstall", help="Uninstalls git hooks")
    sp_uninstall.set_defaults(func=uninstall)

    sp_reverse = sp.add_parser("reverse", help="Reverses migrations")
    sp_reverse.add_argument("--dst-branch", required=True)
    sp_reverse.set_defaults(func=reverse_migrations)

    try:
        args = parser.parse_args()
        args.func(args)
    except AttributeError:
        parser.print_help()


if __name__ == "__main__":
    main()
