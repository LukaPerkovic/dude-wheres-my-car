from unittest.mock import patch
from src.mcp_server import server


def test_write_rejects_empty_fields():
    with patch.object(server, "MCP_AUTH_TOKEN", ""):
        result = server.write_reservation("", "ABC", "period", "now")
        assert result.startswith("ERROR")


def test_write_success(tmp_path):
    with (
        patch.object(server, "MCP_AUTH_TOKEN", ""),
        patch.object(server, "DATA_DIR", tmp_path),
        patch.object(server, "RESERVATIONS_FILE", tmp_path / "out.txt"),
    ):
        result = server.write_reservation(
            "Alice", "NL-99", "June 1-3", "2025-05-30T12:00:00Z"
        )
        assert result.startswith("OK")
        assert "Alice | NL-99" in (tmp_path / "out.txt").read_text()


def test_write_rejects_bad_token():
    with patch.object(server, "MCP_AUTH_TOKEN", "real-secret"):
        result = server.write_reservation(
            "Alice", "NL-99", "June", "now", auth_token="wrong"
        )
        assert result.startswith("ERROR")
