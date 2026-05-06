import pytest
from unittest.mock import patch
from src.db.file_writer import ReservationWriter


def test_writer_success():
    writer = ReservationWriter(server_url="http://fake:8000/sse")
    with patch.object(writer.client, "write_reservation", return_value="OK: Saved."):
        writer.write_reservation("John", "ABC-1", "Feb 1-5", "2025-01-31T10:00:00Z")


def test_writer_raises_on_error():
    writer = ReservationWriter(server_url="http://fake:8000/sse")
    with patch.object(
        writer.client, "write_reservation", return_value="ERROR: Unauthorized."
    ):
        with pytest.raises(RuntimeError, match="Unauthorized"):
            writer.write_reservation("John", "ABC-1", "Feb 1-5", "2025-01-31T10:00:00Z")
