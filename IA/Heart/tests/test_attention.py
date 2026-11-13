"""HEART_005 forward-only causal-attention correctness and safety tests."""
import math
import unittest

from heart.neural import BPETokenizer, TokenEmbeddings, CausalAttention


class CausalAttentionTests(unittest.TestCase):
    def setUp(self):
        self.embeddings = TokenEmbeddings(330, dimension=8, seed=7)
        self.layer = CausalAttention(dimension=8, seed=17, max_tokens=48)

    def test_causal_mask_is_strictly_lower_triangular(self):
        output = self.layer.forward([10, 11, 12, 13], self.embeddings)
        self.assertEqual(len(output.weights), 4)
        self.assertEqual(len(output.vectors), 4)
        for i, row in enumerate(output.weights):
            self.assertEqual(len(row), 4)
            self.assertAlmostEqual(sum(row), 1.0, places=12)
            self.assertTrue(all(math.isfinite(x) and 0 <= x <= 1 for x in row))
            for j in range(i+1, len(row)):
                self.assertEqual(row[j], 0.0)
            self.assertEqual(len(output.vectors[i]), 8)
            self.assertTrue(all(math.isfinite(x) for x in output.vectors[i]))

    def test_prefix_invariance_future_tokens_cannot_affect_past(self):
        prefix = [10, 30, 27]
        prefix_out = self.layer.forward(prefix, self.embeddings)
        longer_out = self.layer.forward(prefix + [125, 126, 127], self.embeddings)
        for index in range(len(prefix)):
            self.assertEqual(prefix_out.vectors[index], longer_out.vectors[index])
            self.assertEqual(prefix_out.weights[index],
                             longer_out.weights[index][:len(prefix)])
        modified = self.layer.forward(prefix + [100, 1, 20], self.embeddings)
        for index in range(len(prefix)):
            self.assertEqual(prefix_out.vectors[index], modified.vectors[index])

    def test_pad_queries_and_keys_do_not_participate(self):
        ids = [BPETokenizer.PAD_ID, 9, 10, BPETokenizer.PAD_ID, 11]
        result = self.layer.forward(ids, self.embeddings)
        self.assertEqual(result.weights[0], (0., 0., 0., 0., 0.))
        self.assertEqual(result.vectors[0], (0.,) * 8)
        self.assertEqual(result.weights[3], (0., 0., 0., 0., 0.))
        self.assertEqual(result.vectors[3], (0.,) * 8)
        for index in (1, 2, 4):
            self.assertEqual(result.weights[index][0], 0.)
            self.assertEqual(result.weights[index][3], 0.)
            self.assertAlmostEqual(sum(result.weights[index]), 1., places=12)

    def test_reproducible_seed_and_no_weight_mutation(self):
        before = self.embeddings.lookup([42, 43])
        output1 = self.layer.forward([42, 43, 42], self.embeddings)
        output2 = CausalAttention(8, seed=17).forward([42, 43, 42], self.embeddings)
        self.assertEqual(output1, output2)
        different = CausalAttention(8, seed=99).forward([42, 43, 42], self.embeddings)
        self.assertNotEqual(output1.vectors, different.vectors)
        self.assertEqual(before, self.embeddings.lookup([42, 43]))

    def test_position_encoding_changes_repeated_token_outputs(self):
        ids = [7, 7, 7]
        with_pos = self.layer.forward(ids, self.embeddings, add_positions=True)
        no_pos = self.layer.forward(ids, self.embeddings, add_positions=False)
        self.assertNotEqual(with_pos.vectors, no_pos.vectors)
        for lhs, rhs in zip(no_pos.vectors[0], no_pos.vectors[1]):
            self.assertAlmostEqual(lhs, rhs, places=12)
        for lhs, rhs in zip(no_pos.vectors[1], no_pos.vectors[2]):
            self.assertAlmostEqual(lhs, rhs, places=12)

    def test_tokenizer_and_trained_embeddings_integration(self):
        tokenizer = BPETokenizer()
        tokenizer.train(["heartai pesquisa linguagem", "linguagem neural coração"] * 5, vocab_size=280)
        model = TokenEmbeddings(tokenizer.vocab_size, dimension=8, seed=3)
        rows = [tokenizer.encode(t) for t in ["heartai", "linguagem", "coração"]]
        model.fit(rows * 2, epochs=2, window=1, negatives=1)
        ids = tokenizer.encode("Olá, HeartAI!")[:16]
        result = self.layer.forward(ids, model)
        self.assertEqual(result.token_ids, tuple(ids))
        self.assertEqual(len(result.weights), len(ids))
        self.assertTrue(all(math.isfinite(x) for row in result.vectors for x in row))

    def test_bounds_errors_and_overflow_rejection(self):
        bad_args = [dict(dimension=1), dict(dimension=65),
                    dict(max_tokens=0), dict(max_tokens=65)]
        for kwargs in bad_args:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                CausalAttention(**kwargs)
        with self.assertRaises(TypeError):
            CausalAttention(seed=True)
        for ids in ([], [1]*49, [False], [-1], [330], [1.5]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.layer.forward(ids, self.embeddings)
        with self.assertRaises(TypeError):
            self.layer.forward("abc", self.embeddings)
        with self.assertRaises(TypeError):
            self.layer.forward([1], self.embeddings, add_positions=1)
        with self.assertRaises(ValueError):
            self.layer.forward([1], TokenEmbeddings(330, 12))
        self.embeddings.input_weights[5][0] = float("inf")
        with self.assertRaises(ValueError):
            self.layer.forward([5], self.embeddings)
        self.embeddings.input_weights[5][0] = 1e12
        with self.assertRaises(ValueError):
            self.layer.forward([5], self.embeddings)

    def test_max_length_and_all_padding(self):
        attention = CausalAttention(8, seed=17, max_tokens=64)
        all_pad = attention.forward([256]*8, self.embeddings)
        self.assertEqual(all_pad.weights, ((0.,)*8,)*8)
        self.assertEqual(all_pad.vectors, ((0.,)*8,)*8)
        result = attention.forward(list(range(64)), self.embeddings)
        self.assertEqual(len(result.vectors), 64)
        self.assertAlmostEqual(sum(result.weights[-1]), 1., places=12)


if __name__ == "__main__":
    unittest.main()
