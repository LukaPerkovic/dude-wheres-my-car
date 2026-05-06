"""Discover LangGraph threads currently paused at an interrupt."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass
class PendingReservation:
    thread_id: str
    reservation_id: str | None
    name: str
    surname: str
    plate: str
    date_start: str
    date_end: str


def list_pending_reservations(graph, sqlite_path: str) -> list[PendingReservation]:
    """
    Returns reservations waiting for admin approval.

    We get the set of thread_ids from the checkpoint DB, then use the graph's
    own API to filter to those actually at an interrupt and read their state.
    """
    thread_ids = _distinct_thread_ids(sqlite_path)

    pending: list[PendingReservation] = []
    for tid in thread_ids:
        config = {"configurable": {"thread_id": tid}}
        try:
            snapshot = graph.get_state(config)
        except Exception:
            continue

        if not snapshot.next:
            continue  # not waiting at an interrupt

        values: dict[str, Any] = snapshot.values or {}
        reservation = values.get("reservation") or {}

        pending.append(
            PendingReservation(
                thread_id=tid,
                reservation_id=values.get("reservation_id"),
                name=reservation.get("name", ""),
                surname=reservation.get("surname", ""),
                plate=reservation.get("vehicle_plate", ""),
                date_start=str(reservation.get("date_start", "")),
                date_end=str(reservation.get("date_end", "")),
            )
        )
    return pending


def _distinct_thread_ids(sqlite_path: str) -> list[str]:
    conn = sqlite3.connect(sqlite_path)
    try:
        cur = conn.execute(
            "SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id"
        )
        return [row[0] for row in cur.fetchall()]
    except sqlite3.OperationalError:
        # Table doesn't exist yet (no conversations happened)
        return []
    finally:
        conn.close()
