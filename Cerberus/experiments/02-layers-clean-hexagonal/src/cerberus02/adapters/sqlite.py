"""SQLite outbound adapter. Bound parameters and local file only."""
from pathlib import Path
import sqlite3
from ..domain import Reservation


class SQLiteReservations:
    def __init__(self, path: str | Path):
        self._connection = sqlite3.connect(str(path))
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                event_code TEXT NOT NULL,
                guest_name TEXT NOT NULL,
                seats INTEGER NOT NULL CHECK(seats BETWEEN 1 AND 6)
            )
        """)
        self._connection.commit()

    def add(self, reservation: Reservation) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO reservations(reservation_id,event_code,guest_name,seats) VALUES (?,?,?,?)",
                (reservation.reservation_id, reservation.event_code,
                 reservation.guest_name, reservation.seats),
            )

    def get(self, reservation_id: str) -> Reservation | None:
        row = self._connection.execute(
            "SELECT reservation_id,event_code,guest_name,seats FROM reservations WHERE reservation_id=?",
            (reservation_id,),
        ).fetchone()
        return Reservation(*row) if row else None

    def close(self) -> None:
        self._connection.close()
