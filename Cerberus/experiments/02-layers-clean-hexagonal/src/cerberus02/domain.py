"""Domain layer: rules independent of databases and delivery channels."""
from dataclasses import dataclass
import re


class DomainValidationError(ValueError):
    """A business invariant was violated."""


@dataclass(frozen=True, slots=True)
class Reservation:
    reservation_id: str
    event_code: str
    guest_name: str
    seats: int

    @classmethod
    def create(cls, reservation_id: str, event_code: str, guest_name: str, seats: int):
        if not isinstance(reservation_id, str) or not reservation_id.strip():
            raise DomainValidationError("reservation_id is required")
        if not isinstance(event_code, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", event_code):
            raise DomainValidationError("event_code must be 3–32 ASCII letters, numbers, _ or -")
        if not isinstance(guest_name, str) or not (2 <= len(guest_name.strip()) <= 80):
            raise DomainValidationError("guest_name must contain 2–80 characters")
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in guest_name):
            raise DomainValidationError("guest_name cannot contain control characters")
        if type(seats) is not int or not 1 <= seats <= 6:
            raise DomainValidationError("seats must be an integer between 1 and 6")
        return cls(reservation_id.strip(), event_code, guest_name.strip(), seats)
