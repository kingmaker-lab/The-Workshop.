"""In-memory outbound adapter, useful for tests and disposable runs."""
from ..domain import Reservation


class InMemoryReservations:
    def __init__(self):
        self._records: dict[str, Reservation] = {}

    def add(self, reservation: Reservation) -> None:
        if reservation.reservation_id in self._records:
            raise ValueError("duplicate reservation id")
        self._records[reservation.reservation_id] = reservation

    def get(self, reservation_id: str) -> Reservation | None:
        return self._records.get(reservation_id)
