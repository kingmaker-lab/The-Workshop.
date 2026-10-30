"""Wolfpack Academy API v0.1: read-only lessons and stateless answer checks.

This starter does not run student-submitted code, issue tokens or store personal data.
"""
import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Wolfpack Academy API",
    description="MVP de desafios educativos da The Workshop (sem execucao de codigo).",
    version="0.1.0",
)

_origins = [s.strip() for s in os.getenv(
    "ALLOWED_ORIGINS", "https://wolfpack.wolfpackworkshop.workers.dev"
).split(",") if s.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class Choice(BaseModel):
    id: str
    text: str

class ChallengePublic(BaseModel):
    id: str
    game_id: str
    title: str
    prompt: str
    language: str
    difficulty: Literal["beginner", "intermediate"]
    choices: list[Choice]

class ChallengeInternal(ChallengePublic):
    answer: str
    explanation: str

class AnswerInput(BaseModel):
    choice_id: str = Field(min_length=1, max_length=24, pattern=r"^[a-z0-9_-]+$")

class AnswerResult(BaseModel):
    correct: bool
    correct_choice_id: str
    explanation: str

GAMES = [
    {"id": "logic", "title": "Logica de programacao", "description": "Interprete programas sem executar codigo."},
    {"id": "debug", "title": "Encontre o bug", "description": "Investigue erros comuns e aprenda a corrigi-los."},
]

CHALLENGES = [
    ChallengeInternal(id="logic-001", game_id="logic", title="Condicional em Python", language="python", difficulty="beginner",
        prompt="O que imprime `print(3 > 2)`?", choices=[Choice(id="a", text="True"), Choice(id="b", text="False"), Choice(id="c", text="3")],
        answer="a", explanation="O operador > compara valores e devolve um booleano; 3 e maior que 2."),
    ChallengeInternal(id="logic-002", game_id="logic", title="Indice de listas", language="python", difficulty="beginner",
        prompt="Com `itens = ['a', 'b', 'c']`, qual o valor de `itens[1]`?", choices=[Choice(id="a", text="a"), Choice(id="b", text="b"), Choice(id="c", text="c")],
        answer="b", explanation="Em Python os indices comecam em zero: itens[0]='a' e itens[1]='b'."),
    ChallengeInternal(id="logic-003", game_id="logic", title="Loop simples", language="python", difficulty="beginner",
        prompt="Quantas vezes executa o corpo de `for i in range(3):`?", choices=[Choice(id="a", text="2"), Choice(id="b", text="3"), Choice(id="c", text="4")],
        answer="b", explanation="range(3) produz 0, 1 e 2: tres iteracoes."),
    ChallengeInternal(id="debug-001", game_id="debug", title="Comparacao ou atribuicao?", language="javascript", difficulty="beginner",
        prompt="Em `if (age = 18)`, qual erro precisa ser corrigido?", choices=[Choice(id="a", text="Usar comparacao (===) em vez de atribuicao (=)"), Choice(id="b", text="Remover os parenteses"), Choice(id="c", text="Trocar 18 por '18'")],
        answer="a", explanation="O sinal = atribui valor. Para comparar tipo e valor em JavaScript, use ===."),
    ChallengeInternal(id="debug-002", game_id="debug", title="Fora dos limites", language="python", difficulty="beginner",
        prompt="Com `nums = [10, 20]`, o que acontece ao acessar `nums[2]`?", choices=[Choice(id="a", text="Retorna 20"), Choice(id="b", text="Retorna None"), Choice(id="c", text="Lanca IndexError")],
        answer="c", explanation="A lista possui indices 0 e 1. Acessar o indice 2 gera IndexError."),
]
BY_ID = {challenge.id: challenge for challenge in CHALLENGES}


def get_challenge(challenge_id: str) -> ChallengeInternal:
    challenge = BY_ID.get(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@app.get("/health")
def health():
    return {"status": "ok", "service": "wolfpack-academy-api", "version": "0.1.0"}


@app.get("/api/v1/games")
def games():
    return GAMES


@app.get("/api/v1/challenges", response_model=list[ChallengePublic])
def challenges(game_id: str | None = None):
    if game_id is not None and game_id not in {g["id"] for g in GAMES}:
        raise HTTPException(status_code=404, detail="Game not found")
    return [c for c in CHALLENGES if game_id is None or c.game_id == game_id]


@app.get("/api/v1/challenges/{challenge_id}", response_model=ChallengePublic)
def challenge_detail(challenge_id: str):
    return get_challenge(challenge_id)


@app.post("/api/v1/challenges/{challenge_id}/check", response_model=AnswerResult)
def check_answer(challenge_id: str, answer: AnswerInput):
    challenge = get_challenge(challenge_id)
    if answer.choice_id not in {c.id for c in challenge.choices}:
        raise HTTPException(status_code=422, detail="Choice not present in challenge")
    return AnswerResult(
        correct=answer.choice_id == challenge.answer,
        correct_choice_id=challenge.answer,
        explanation=challenge.explanation,
    )
