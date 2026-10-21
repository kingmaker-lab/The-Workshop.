import unittest
from cerberus02.domain import Reservation, DomainValidationError
from cerberus02.usecases import CreateReservation, CreateReservationCommand, GetReservation, ReservationNotFound
from cerberus02.adapters.memory import InMemoryReservations


class TestIds:
    def __init__(self):
        self.count = 0

    def new_id(self):
        self.count += 1
        return f"test-{self.count}"


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryReservations()
        self.ids = TestIds()
        self.create = CreateReservation(self.repo, self.ids)

    def test_happy_path(self):
        res = self.create.execute(CreateReservationCommand("wolfcon_2026", "Ada", 2))
        self.assertEqual(res.reservation_id, "test-1")
        self.assertEqual(GetReservation(self.repo).execute(res.reservation_id), res)

    def test_invalid_seats_do_not_persist(self):
        for seats in (-1, 0, 7, 1.1, True):
            with self.subTest(seats=seats):
                with self.assertRaises(DomainValidationError):
                    self.create.execute(CreateReservationCommand("conf2026", "Ada", seats))
        self.assertIsNone(self.repo.get("test-1"))

    def test_input_checks(self):
        for event, guest in [("../etc/passwd", "Ada"), ("conf2026", "A"),
                              ("conf2026", "Ada\nAdmin"), ("", "Ada")]:
            with self.subTest(event=event, guest=guest):
                with self.assertRaises(DomainValidationError):
                    self.create.execute(CreateReservationCommand(event, guest, 2))

    def test_immutability(self):
        record = self.create.execute(CreateReservationCommand("conf2026", "Ada", 1))
        with self.assertRaises(AttributeError):
            record.seats = 99

    def test_not_found(self):
        with self.assertRaises(ReservationNotFound):
            GetReservation(self.repo).execute("missing")


if __name__ == "__main__":
    unittest.main()
