import test from "node:test";
import assert from "node:assert/strict";
import { Schedule, standardPolicy, smallGroupPolicy } from "./domain.mjs";
import { ReserveSeats, InMemoryScheduleStore } from "./application.mjs";
import { toNotificationDraft } from "./communications.mjs";

function setup(policy = standardPolicy, capacity = 8) {
  const store = new InMemoryScheduleStore([new Schedule({ eventCode: "wolfcon", capacity })]);
  return { store, useCase: new ReserveSeats({ store, policy }) };
}

test("aggregate reserves seats and emits immutable domain event", () => {
  const { store, useCase } = setup();
  const result = useCase.execute({ eventCode: "wolfcon", bookingId: "r001", seats: 4 });
  assert.equal(result.created, true);
  assert.equal(result.occupied, 4);
  assert.equal(store.events().length, 1);
  assert.equal(store.events()[0].type, "reservation.created.v1");
  assert.ok(Object.isFrozen(store.events()[0]));
});

test("aggregate prevents overbooking in sequential process", () => {
  const { store, useCase } = setup(standardPolicy, 7);
  useCase.execute({ eventCode: "wolfcon", bookingId: "a", seats: 4 });
  assert.throws(() => useCase.execute({ eventCode: "wolfcon", bookingId: "b", seats: 4 }), /not enough capacity/);
  assert.equal(store.load("wolfcon").occupied, 4);
  assert.equal(store.events().length, 1);
});

test("same request is idempotent; conflicting ID rejected", () => {
  const { store, useCase } = setup();
  const cmd = { eventCode: "wolfcon", bookingId: "r001", seats: 2 };
  assert.equal(useCase.execute(cmd).created, true);
  assert.equal(useCase.execute(cmd).created, false);
  assert.throws(() => useCase.execute({ ...cmd, seats: 3 }), /conflict/);
  assert.equal(store.events().length, 1);
  assert.equal(store.load("wolfcon").occupied, 2);
});

test("Strategy swaps policy without rewriting the use case", () => {
  const standard = setup(standardPolicy), small = setup(smallGroupPolicy);
  const cmd = { eventCode: "wolfcon", bookingId: "r001", seats: 4 };
  assert.equal(standard.useCase.execute(cmd).created, true);
  assert.throws(() => small.useCase.execute(cmd), /policy/);
  assert.equal(small.store.events().length, 0);
});

test("invalid booking and missing schedule do not mutate state", () => {
  const { store, useCase } = setup();
  assert.throws(() => useCase.execute({ eventCode: "unknown", bookingId: "r1", seats: 1 }), /unknown/);
  assert.throws(() => useCase.execute({ eventCode: "wolfcon", bookingId: "../invalid", seats: 1 }));
  assert.throws(() => useCase.execute({ eventCode: "wolfcon", bookingId: "r1", seats: true }));
  assert.equal(store.load("wolfcon").occupied, 0);
});

test("domain rejects invalid pre-existing state", () => {
  assert.throws(() => new Schedule({ eventCode: "wolfcon", capacity: 1, bookings: { a: 2 } }), /capacity/);
  assert.throws(() => new Schedule({ eventCode: "wolfcon", capacity: 3, bookings: { a: 1.5 } }));
  assert.throws(() => new Schedule({ eventCode: "../bad", capacity: 5 }));
});

test("anti-corruption adapter builds DTO without leaking domain internals", () => {
  const { store, useCase } = setup();
  useCase.execute({ eventCode: "wolfcon", bookingId: "r1", seats: 2 });
  const draft = toNotificationDraft(store.events()[0]);
  assert.equal(draft.kind, "notification.preview.v1");
  assert.equal(draft.reference, "r1");
  assert.equal(draft.summary, "2 seat(s) reserved for wolfcon");
  assert.ok(Object.isFrozen(draft));
  assert.throws(() => toNotificationDraft({ type: "payment.paid.v1" }), /unsupported/);
  assert.throws(() => toNotificationDraft({
    type: "reservation.created.v1", eventCode: "<script>", bookingId: "r1", seats: 1,
  }), /invalid/);
});

test("store refuses inconsistent aggregate/event pair", () => {
  const store = new InMemoryScheduleStore([new Schedule({ eventCode: "wolfcon", capacity: 8 })]);
  assert.throws(() => store.commit(store.load("wolfcon"), {
    type: "reservation.created.v1", eventCode: "wolfcon", bookingId: "r1", seats: 2,
  }), /inconsistency/);
  assert.equal(store.events().length, 0);
});
