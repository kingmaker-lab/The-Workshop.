// Separate Communications bounded context. Do not import aggregate internals.
// This anti-corruption adapter maps a public event contract to a local DTO.
export function toNotificationDraft(event) {
  if (event?.type !== "reservation.created.v1")
    throw new TypeError("unsupported contract");
  for (const key of ["eventCode", "bookingId"]) {
    if (typeof event[key] !== "string" || !/^[A-Za-z0-9_-]{1,64}$/.test(event[key]))
      throw new TypeError("invalid event contract: " + key);
  }
  if (!Number.isSafeInteger(event.seats) || event.seats < 1 || event.seats > 6)
    throw new TypeError("invalid event contract: seats");
  return Object.freeze({
    kind: "notification.preview.v1", reference: event.bookingId,
    summary: event.seats + " seat(s) reserved for " + event.eventCode,
  });
}
// Preview only: no messages sent, no contact info, no external endpoints.
