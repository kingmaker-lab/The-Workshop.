import test from "node:test";
import assert from "node:assert/strict";
import { createLocalModel, createEventModel } from "./model.mjs";

const sample = { requestId: "req-001", eventCode: "workshop2026", seats: 2 };

test("local model performs notification synchronously", () => {
  const model = createLocalModel();
  model.reserve(sample);
  assert.equal(model.reservations.size, 1);
  assert.deepEqual(model.notifications, [{ id: sample.requestId, eventCode: sample.eventCode }]);
});

test("event model records a pending notification until dispatch", () => {
  const model = createEventModel();
  model.reserve(sample);
  assert.equal(model.notifications.length, 0);
  assert.equal(model.outbox.get(sample.requestId).acknowledged, false);
  assert.equal(model.dispatch(), 1);
  assert.equal(model.notifications.length, 1);
  assert.equal(model.outbox.get(sample.requestId).acknowledged, true);
});

test("retry after acknowledgement loss does not repeat the side effect", () => {
  const model = createEventModel();
  model.reserve(sample);
  assert.throws(() => model.dispatch({ failAfterDelivery: true }), /acknowledgement/);
  assert.equal(model.notifications.length, 1);
  assert.equal(model.outbox.get(sample.requestId).acknowledged, false);
  assert.equal(model.dispatch(), 1);
  assert.equal(model.notifications.length, 1);
  assert.equal(model.deliveryAttempts.length, 2);
});

test("transport failure before delivery leaves event pending", () => {
  const model = createEventModel();
  model.reserve(sample);
  assert.throws(() => model.dispatch({ failBeforeDelivery: true }), /transport/);
  assert.equal(model.notifications.length, 0);
  assert.equal(model.dispatch(), 1);
  assert.equal(model.notifications.length, 1);
});

test("repeated requestId is idempotent, but conflicting payload is rejected", () => {
  for (const factory of [createLocalModel, createEventModel]) {
    const model = factory();
    const first = model.reserve(sample);
    assert.equal(model.reserve({ ...sample }), first);
    assert.equal(model.reservations.size, 1);
    assert.throws(() => model.reserve({ ...sample, seats: 3 }), /conflict/);
  }
});

test("invalid inputs are rejected without side effects", () => {
  for (const factory of [createLocalModel, createEventModel]) {
    const model = factory();
    for (const invalid of [
      { ...sample, seats: 0 },
      { ...sample, seats: 1.5 },
      { ...sample, eventCode: "../escape" },
      { ...sample, requestId: "" },
    ]) {
      assert.throws(() => model.reserve(invalid));
    }
    assert.equal(model.reservations.size, 0);
  }
});

test("an acknowledged event is not delivered again", () => {
  const model = createEventModel();
  model.reserve(sample);
  assert.equal(model.dispatch(), 1);
  assert.equal(model.dispatch(), 0);
  assert.equal(model.deliveryAttempts.length, 1);
});
