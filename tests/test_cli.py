from unittest.mock import (
    MagicMock,
    patch,
)

from great_scott.__main__ import main


class TestCLI:
    def test_install_subcommand_calls_install(self):
        mock_fn = MagicMock()
        with patch("great_scott.__main__.install", mock_fn), patch(
            "sys.argv", ["great-scott", "install"]
        ):
            main()
        mock_fn.assert_called_once()

    def test_uninstall_subcommand_calls_uninstall(self):
        mock_fn = MagicMock()
        with patch("great_scott.__main__.uninstall", mock_fn), patch(
            "sys.argv", ["great-scott", "uninstall"]
        ):
            main()
        mock_fn.assert_called_once()

    def test_reverse_subcommand_passes_dst_branch(self):
        mock_fn = MagicMock()
        with patch("great_scott.__main__.reverse_migrations", mock_fn), patch(
            "sys.argv", ["great-scott", "reverse", "--dst-branch", "main"]
        ):
            main()
        args = mock_fn.call_args[0][0]
        assert args.dst_branch == "main"

    def test_no_subcommand_prints_help(self, capsys):
        with patch("sys.argv", ["great-scott"]):
            main()
        out = capsys.readouterr().out
        assert "usage" in out.lower()
