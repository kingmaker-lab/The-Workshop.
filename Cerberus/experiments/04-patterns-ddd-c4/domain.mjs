// CERBERUS_04: reservations bounded context (sequential, in-memory model).
// No inventory locking, authentication, payments or concurrency guarantees.
const SAFE_ID = /^[A-Za-z0-9_-]{1,64}$/;
function validId(value, label) {
  if (typeof value !== "string" || !SAFE_ID.test(value)) {
    throw new RangeError(label + ": expected 1..64 ASCII letters, digits, _ or -");
  }
}
export const standardPolicy = Object.freeze({ name: "standard", maxSeatsPerReservation: 6 });
export const smallGroupPolicy = Object.freeze({ name: "small-group", maxSeatsPerReservation: 3 });

export class Schedule {
  constructor({ eventCode, capacity, bookings = {} }) {
    validId(eventCode, "eventCode");
    if (!Number.isSafeInteger(capacity) || capacity < 1)
      throw new RangeError("capacity must be a positive safe integer");
    if (!bookings || Array.isArray(bookings) || typeof bookings !== "object")
      throw new TypeError("bookings must be an object");
    const copy = Object.create(null);
    let used = 0;
    for (const [id, seats] of Object.entries(bookings)) {
      validId(id, "bookingId");
      if (!Number.isSafeInteger(seats) || seats < 1)
        throw new RangeError("every booking must have positive integer seats");
      used += seats;
    }
    if (!Number.isSafeInteger(used) || used > capacity)
      throw new RangeError("bookings exceed event capacity");
    Object.assign(copy, bookings);
    Object.freeze(copy);
    this.eventCode = eventCode;
    this.capacity = capacity;
    this.bookings = copy;
    Object.freeze(this);
  }
  get occupied() {
    return Object.values(this.bookings).reduce((sum, seats) => sum + seats, 0);
  }
  reserve({ bookingId, seats }, policy) {
    validId(bookingId, "bookingId");
    if (!policy || !Number.isSafeInteger(policy.maxSeatsPerReservation)
        || policy.maxSeatsPerReservation < 1)
      throw new TypeError("capacity strategy required");
    if (!Number.isSafeInteger(seats) || seats < 1 || seats > policy.maxSeatsPerReservation)
      throw new RangeError("seats outside selected policy");
    if (Object.hasOwn(this.bookings, bookingId)) {
      if (this.bookings[bookingId] !== seats) throw new Error("bookingId conflict");
      return { schedule: this, event: null, created: false };
    }
    if (this.occupied + seats > this.capacity) throw new RangeError("not enough capacity");
    const next = new Schedule({
      eventCode: this.eventCode, capacity: this.capacity,
      bookings: { ...this.bookings, [bookingId]: seats },
    });
    const event = Object.freeze({
      type: "reservation.created.v1", eventCode: this.eventCode, bookingId, seats,
    });
    return { schedule: next, event, created: true };
  }
}
