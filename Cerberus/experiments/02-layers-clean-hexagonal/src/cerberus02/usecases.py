"""Application layer: orchestrates domain rules through abstract ports."""
from dataclasses import dataclass
from .domain import Reservation
from .ports import ReservationRepository, IdGenerator


class ReservationNotFound(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class CreateReservationCommand:
    event_code: str
    guest_name: str
    seats: int


class CreateReservation:
    def __init__(self, repository: ReservationRepository, id_generator: IdGenerator):
        self._repository = repository
        self._ids = id_generator

    def execute(self, command: CreateReservationCommand) -> Reservation:
        # Domain checks must precede the persistence side effect.
        reservation = Reservation.create(
            self._ids.new_id(), command.event_code, command.guest_name, command.seats
        )
        self._repository.add(reservation)
        return reservation


class GetReservation:
    def __init__(self, repository: ReservationRepository):
        self._repository = repository

    def execute(self, reservation_id: str) -> Reservation:
        found = self._repository.get(reservation_id)
        if found is None:
            raise ReservationNotFound("reservation not found")
        return found
