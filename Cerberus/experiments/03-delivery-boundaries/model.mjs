// CERBERUS 03: delivery boundaries, educational in-process model.
// This is NOT a networked microservice or a durable message broker.
function check(command) {
  if (!command || typeof command !== "object") throw new TypeError("Command is required");
  const { requestId, eventCode, seats } = command;
  if (typeof requestId !== "string" || !/^[a-zA-Z0-9_-]{1,64}$/.test(requestId))
    throw new RangeError("requestId must contain 1-64 safe characters");
  if (typeof eventCode !== "string" || !/^[a-zA-Z0-9_-]{1,64}$/.test(eventCode))
    throw new RangeError("eventCode must contain 1-64 safe characters");
  if (!Number.isInteger(seats) || seats < 1 || seats > 6)
    throw new RangeError("seats must be an integer between 1 and 6");
}

function reservation(command) {
  return Object.freeze({
    id: command.requestId,
    eventCode: command.eventCode,
    seats: command.seats,
  });
}

// Model A: one in-process boundary, synchronous notification side effect.
// No real database transaction is implied by this example.
export function createLocalModel() {
  const reservations = new Map();
  const notifications = [];
  return {
    reservations,
    notifications,
    reserve(command) {
      check(command);
      const existing = reservations.get(command.requestId);
      if (existing) {
        if (existing.eventCode !== command.eventCode || existing.seats !== command.seats)
          throw new Error("requestId conflict");
        return existing;
      }
      const item = reservation(command);
      reservations.set(item.id, item);
      notifications.push({ id: item.id, eventCode: item.eventCode });
      return item;
    },
  };
}

// Model B: message-boundary simulation with a pending outbox, ack and retry.
// Every component is in the same process. No disk/network or process isolation.
export function createEventModel() {
  const reservations = new Map();
  const outbox = new Map();
  const processed = new Set();
  const notifications = [];
  const deliveryAttempts = [];
  return {
    reservations,
    outbox,
    notifications,
    deliveryAttempts,
    reserve(command) {
      check(command);
      const existing = reservations.get(command.requestId);
      if (existing) {
        if (existing.eventCode !== command.eventCode || existing.seats !== command.seats)
          throw new Error("requestId conflict");
        return existing;
      }
      const item = reservation(command);
      reservations.set(item.id, item);
      outbox.set(item.id, { event: { id: item.id, eventCode: item.eventCode }, acknowledged: false });
      return item;
    },
    dispatch({ failBeforeDelivery = false, failAfterDelivery = false } = {}) {
      let acknowledged = 0;
      for (const [id, entry] of outbox) {
        if (entry.acknowledged) continue;
        if (failBeforeDelivery) throw new Error("simulated transport failure");
        deliveryAttempts.push(id);
        // Idempotent consumer: a repeated delivery is not a repeated side effect.
        if (!processed.has(id)) {
          processed.add(id);
          notifications.push({ ...entry.event });
        }
        if (failAfterDelivery) throw new Error("simulated acknowledgement failure");
        entry.acknowledged = true;
        acknowledged++;
      }
      return acknowledged;
    },
  };
}
