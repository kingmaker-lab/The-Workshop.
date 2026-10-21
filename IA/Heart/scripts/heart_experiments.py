"""Run HEART_002 and HEART_003 as a local research demo."""
from __future__ import annotations

import argparse
from pathlib import Path

from heart.conversation import ConversationStore
from heart.neural import BPETokenizer


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
    finally:
        memory.close()


if __name__ == "__main__":
    main()
