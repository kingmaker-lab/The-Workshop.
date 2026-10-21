"""HTTP-shaped inbound adapter: pure controller, intentionally NO listening server.

Return a transport-shaped response from a dict. Real HTTP hosting needs separate
authentication, authorization, CSRF/abuse controls, TLS and operational limits.
"""
from dataclasses import asdict, dataclass
from collections.abc import Mapping
from ..domain import DomainValidationError
from ..usecases import (
    CreateReservation, CreateReservationCommand, GetReservation, ReservationNotFound
)


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status: int
    body: dict


class ReservationJsonController:
    def __init__(self, create: CreateReservation, get: GetReservation):
        self._create = create
        self._get = get

    def post(self, payload: object) -> ApiResponse:
        if not isinstance(payload, Mapping):
            return ApiResponse(400, {"error": "JSON object expected"})
        if set(payload) != {"event_code", "guest_name", "seats"}:
            return ApiResponse(400, {"error": "unexpected or missing fields"})
        try:
            reservation = self._create.execute(CreateReservationCommand(**payload))
        except DomainValidationError as exc:
            return ApiResponse(422, {"error": str(exc)})
        return ApiResponse(201, asdict(reservation))

    def get(self, reservation_id: str) -> ApiResponse:
        try:
            result = self._get.execute(reservation_id)
        except ReservationNotFound:
            return ApiResponse(404, {"error": "reservation not found"})
        return ApiResponse(200, asdict(result))
