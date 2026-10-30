import math
import unittest

from heart.neural import BPETokenizer, TokenEmbeddings


class Heart004Tests(unittest.TestCase):
    def test_seed_reproducibility_and_copy_safe_lookup(self):
        a = TokenEmbeddings(270, dimension=8, seed=7)
        b = TokenEmbeddings(270, dimension=8, seed=7)
        self.assertEqual(a.lookup([0, 3, 256]), b.lookup([0, 3, 256]))
        vector = a.lookup([0])[0]
        vector[0] = 999
        self.assertNotEqual(a.lookup([0])[0][0], 999)
        self.assertEqual(a.lookup([256]), [[0.0] * 8])

    def test_training_changes_vectors_and_losses_are_finite(self):
        # Context learning is meaningful even when no semantic dataset exists.
        rows = [[1, 2, 1, 2, 3, 2, 1], [1, 3, 1, 2, 3]] * 3
        a = TokenEmbeddings(270, 8, seed=11)
        b = TokenEmbeddings(270, 8, seed=11)
        before = a.lookup([1, 2])
        losses = a.fit(rows, epochs=9, window=2, negatives=1, learning_rate=.2)
        duplicate = b.fit(rows, epochs=9, window=2, negatives=1, learning_rate=.2)
        self.assertEqual(losses, duplicate)
        self.assertEqual(a.lookup([1, 2]), b.lookup([1, 2]))
        self.assertNotEqual(before, a.lookup([1, 2]))
        self.assertEqual(len(losses), 9)
        self.assertTrue(all(math.isfinite(x) and x > 0 for x in losses))
        self.assertLess(losses[-1], losses[0])

    def test_tokenizer_integration_and_cosine(self):
        tokenizer = BPETokenizer()
        tokenizer.train(["heart ai heart ai", "neural ai neural"] * 4, vocab_size=279)
        model = TokenEmbeddings(tokenizer.vocab_size, dimension=8)
        samples = [tokenizer.encode(s) for s in ["heart ai", "neural ai", "heart neural"]]
        loss = model.fit(samples * 2, epochs=3, window=2, negatives=1)
        self.assertEqual(len(loss), 3)
        a = model.mean_pool(tokenizer.encode("heart ai"))
        b = model.mean_pool(tokenizer.encode("neural ai"))
        self.assertEqual(len(a), 8)
        self.assertTrue(-1 <= model.cosine(a, b) <= 1)
        self.assertAlmostEqual(model.cosine(a, a), 1)

    def test_rejects_bad_shape_inputs_and_compute_limits(self):
        invalid_constructors = ((258, 8), (4097, 8), (300, 1), (300, 129))
        for vocab, dim in invalid_constructors:
            with self.subTest(vocab=vocab, dim=dim), self.assertRaises(ValueError):
                TokenEmbeddings(vocab, dim)
        model = TokenEmbeddings(270)
        for ids in ([-1], [300], [True], [1.5]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                model.lookup(ids)
        with self.assertRaises(ValueError):
            model.mean_pool([256, 257, 258])
        with self.assertRaises(ValueError):
            model.fit([[1]])
        with self.assertRaises(ValueError):
            model.fit([[1, 2]], epochs=31)
        with self.assertRaises(ValueError):
            model.fit([[1, 2]], learning_rate=float("nan"))
        with self.assertRaises(ValueError):
            model.fit([list(range(260))] * 10, epochs=30, window=5, negatives=10)
        with self.assertRaises(ValueError):
            model.cosine([float("inf")], [1.0])


if __name__ == "__main__":
    unittest.main()
