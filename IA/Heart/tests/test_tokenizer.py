import tempfile
import unittest
from pathlib import Path

from heart.neural import BPETokenizer


class TokenizerTests(unittest.TestCase):
    def test_utf8_roundtrip(self):
        tokenizer = BPETokenizer()
        tokenizer.train(["coração, coração!", "HeartAI aprende padrões.", "coração!"] * 6, vocab_size=300)
        for text in ("Olá 🦊 ❤️", "ASCII", "日本語", "", "a\x00b"):
            self.assertEqual(tokenizer.decode(tokenizer.encode(text)), text)
        self.assertGreater(tokenizer.vocab_size, 259)

    def test_serialization_and_determinism(self):
        tokenizer = BPETokenizer()
        corpus = ["heart heart heart", "heart ai"]
        tokenizer.train(corpus, vocab_size=280)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokenizer.json"
            tokenizer.save(path)
            loaded = BPETokenizer.load(path)
            self.assertEqual(tokenizer.encode("heart ai"), loaded.encode("heart ai"))
            self.assertEqual(loaded.decode(loaded.encode("heart ai", True)), "heart ai")

    def test_bad_configuration(self):
        with self.assertRaises(ValueError):
            BPETokenizer().train(["test"], vocab_size=100)


if __name__ == "__main__":
    unittest.main()
