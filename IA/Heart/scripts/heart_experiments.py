"""Run HEART_002 through HEART_004 as a local research demo."""
from __future__ import annotations

import argparse
from pathlib import Path

from heart.conversation import ConversationStore
from heart.neural import BPETokenizer, TokenEmbeddings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/heart.db")
    parser.add_argument("--tokenizer", default="data/tokenizer.json")
    args = parser.parse_args()

    memory = ConversationStore(args.db)
    try:
        session_id = memory.create_conversation()
        memory.add_message(session_id, "user", "Olá, Heart!")
        memory.add_message(session_id, "assistant", "HeartAI: protótipo de memória ativo.")
        turns = memory.recent(session_id)
        print(f"HEART_002: sessão {session_id}, {len(turns)} mensagens persistidas")
        corpus = [item["content"] for item in turns] * 10
        tokenizer = BPETokenizer()
        tokenizer.train(corpus, vocab_size=320)
        tokenizer.save(args.tokenizer)
        sample = "Olá, Heart!"
        encoded = tokenizer.encode(sample)
        print(f"HEART_003: vocab={tokenizer.vocab_size}, tokens={encoded}")
        print(f"Roundtrip: {tokenizer.decode(encoded)}")
        print("Nota: tokenizer treinado não equivale a um LLM treinado.")
        # Corpus is a tiny local example, not operational data.
        embeddings = TokenEmbeddings(tokenizer.vocab_size, dimension=8, seed=7)
        rows = [tokenizer.encode(text) for text in corpus]
        losses = embeddings.fit(rows, epochs=3, window=2, negatives=1)
        a = embeddings.mean_pool(tokenizer.encode("Olá, Heart!"))
        b = embeddings.mean_pool(tokenizer.encode("HeartAI"))
        print(f"HEART_004: dimension={embeddings.dimension}, training_loss={losses[-1]:.4f}")
        print(f"Toy cosine similarity: {embeddings.cosine(a, b):.4f}")
        print("Nota: embeddings demonstrativos não são compreensão semântica nem um LLM.")
    finally:
        memory.close()


if __name__ == "__main__":
    main()
