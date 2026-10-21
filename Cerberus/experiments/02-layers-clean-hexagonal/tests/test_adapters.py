from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest
from cerberus02.adapters.ids import UUID4Ids
from cerberus02.adapters.memory import InMemoryReservations
from cerberus02.adapters.sqlite import SQLiteReservations
from cerberus02.adapters.json_api import ReservationJsonController
from cerberus02.usecases import CreateReservation, CreateReservationCommand, GetReservation


class FixedIds:
    def new_id(self):
        return "record-1"


class AdapterContractTests(unittest.TestCase):
    def test_memory_and_sqlite_share_contract(self):
        with TemporaryDirectory() as temp:
            adapters = [InMemoryReservations(), SQLiteReservations(Path(temp) / "demo.db")]
            try:
                for repo in adapters:
                    reservation = CreateReservation(repo, FixedIds()).execute(
                        CreateReservationCommand("conf2026", "Ada Lovelace", 2)
                    )
                    self.assertEqual(GetReservation(repo).execute("record-1"), reservation)
                    self.assertIsNone(repo.get("missing"))
            finally:
                adapters[1].close()

    def test_sqlite_persists_across_connections(self):
        with TemporaryDirectory() as temp:
            location = Path(temp) / "demo.db"
            a = SQLiteReservations(location)
            CreateReservation(a, FixedIds()).execute(CreateReservationCommand("conf2026", "Ada", 1))
            a.close()
            b = SQLiteReservations(location)
            try:
                self.assertEqual(b.get("record-1").guest_name, "Ada")
                with self.assertRaises(sqlite3.IntegrityError):
                    CreateReservation(b, FixedIds()).execute(CreateReservationCommand("conf2026", "Ada", 1))
            finally:
                b.close()

    def test_http_shaped_adapter(self):
        repo = InMemoryReservations()
        controller = ReservationJsonController(CreateReservation(repo, FixedIds()), GetReservation(repo))
        created = controller.post({"event_code":"conf2026","guest_name":"Ada","seats":2})
        self.assertEqual(created.status, 201)
        self.assertEqual(controller.get("record-1").body["seats"], 2)
        self.assertEqual(controller.get("missing").status, 404)
        self.assertEqual(controller.post({"event_code":"conf2026","guest_name":"Ada","seats":8}).status, 422)
        self.assertEqual(controller.post({"event_code":"conf2026","guest_name":"Ada","seats":2,"admin":True}).status, 400)
        self.assertEqual(controller.post(["not a mapping"]).status, 400)


if __name__ == "__main__":
    unittest.main()
