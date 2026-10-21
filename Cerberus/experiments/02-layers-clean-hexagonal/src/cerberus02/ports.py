"""Ports are defined in the core and implemented by adapters."""
from typing import Protocol
from .domain import Reservation


class ReservationRepository(Protocol):
    def add(self, reservation: Reservation) -> None: ...
    def get(self, reservation_id: str) -> Reservation | None: ...


class IdGenerator(Protocol):
    def new_id(self) -> str: ...
