import { Schedule } from "./domain.mjs";

// Port: the application sees only load/commit, never a particular database.
// A production adapter must add atomic writes and concurrency controls.
export class ReserveSeats {
  constructor({ store, policy }) {
    if (!store || typeof store.load !== "function" || typeof store.commit !== "function")
      throw new TypeError("store must implement load and commit");
    if (!policy || !Number.isSafeInteger(policy.maxSeatsPerReservation))
      throw new TypeError("capacity strategy required");
    this.store = store;
    this.policy = policy;
  }
  execute({ eventCode, bookingId, seats } = {}) {
    const schedule = this.store.load(eventCode);
    if (!schedule) throw new RangeError("unknown event");
    const result = schedule.reserve({ bookingId, seats }, this.policy);
    if (result.created) this.store.commit(result.schedule, result.event);
    return Object.freeze({
      eventCode: schedule.eventCode, bookingId, seats, created: result.created,
      occupied: result.schedule.occupied, capacity: result.schedule.capacity,
    });
  }
}

// In-memory adapter, NOT durable storage, nor an ACID implementation.
export class InMemoryScheduleStore {
  #schedules = new Map();
  #events = [];

  constructor(schedules = []) {
    for (const schedule of schedules) {
      if (!(schedule instanceof Schedule)) throw new TypeError("expected Schedule");
      this.#schedules.set(schedule.eventCode, schedule);
    }
  }
  load(eventCode) {
    return this.#schedules.get(eventCode) || null;
  }
  commit(schedule, event) {
    if (!(schedule instanceof Schedule) || event?.type !== "reservation.created.v1")
      throw new TypeError("invalid aggregate/event pair");
    if (event.eventCode !== schedule.eventCode
        || schedule.bookings[event.bookingId] !== event.seats)
      throw new Error("aggregate/event inconsistency");
    this.#schedules.set(schedule.eventCode, schedule);
    this.#events.push(event);
  }
  events() {
    return [...this.#events];
  }
}
