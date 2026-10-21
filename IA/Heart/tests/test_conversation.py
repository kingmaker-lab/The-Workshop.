import tempfile
import unittest
from pathlib import Path

from heart.conversation import ConversationStore


class ConversationTests(unittest.TestCase):
    def test_persistence_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "heart.db"
            store = ConversationStore(path)
            cid = store.create_conversation()
            store.add_message(cid, "user", "Olá, Heart")
            store.add_message(cid, "assistant", "Olá!")
            store.close()
            reopened = ConversationStore(path)
            self.assertEqual(
                [(m["role"], m["content"]) for m in reopened.recent(cid)],
                [("user", "Olá, Heart"), ("assistant", "Olá!")],
            )
            reopened.close()

    def test_sessions_are_isolated_and_search_is_literal(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ConversationStore(Path(tmp) / "heart.db")
            first, second = store.create_conversation(), store.create_conversation()
            store.add_message(first, "user", "100% seguro _ aqui")
            store.add_message(second, "user", "outro diálogo")
            self.assertEqual(len(store.search(first, "100%")), 1)
            self.assertEqual(store.recent(second)[0]["content"], "outro diálogo")
            self.assertEqual(store.search(second, "100%"), [])
            with self.assertRaises(ValueError):
                store.add_message(first, "admin", "teste")
            store.close()


if __name__ == "__main__":
    unittest.main()
