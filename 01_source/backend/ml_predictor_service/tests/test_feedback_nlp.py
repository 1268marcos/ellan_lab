"""Testes leves de NLP (TF-IDF only, sem download de modelos)."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("FEEDBACK_USE_TFIDF_ONLY", "true")

from app.ml_nlp.sentiment_analyzer import analyze_text
from app.ml_nlp.topic_extractor import keyword_topics, lda_topics_batch


def test_analyze_positive_pt():
    r = analyze_text("Adorei o atendimento, excelente experiência!")
    assert r["sentiment_label"] == "positive"
    assert r["user_intent"] in ("elogio", "reclamacao", "sugestao", "urgente")


def test_analyze_negative_pt():
    r = analyze_text("Péssimo, atraso absurdo e suporte inexistente.")
    assert r["sentiment_label"] == "negative"


def test_keyword_topics():
    t = keyword_topics("entrega rápida mas embalagem ruim", top_k=4)
    assert isinstance(t, list)
    assert len(t) <= 4


def test_lda_batch():
    docs = [
        "entrega demorou muito",
        "produto veio errado",
        "ótimo atendimento na loja",
        "sugiro melhorar o app",
        "urgente preciso do pedido hoje",
    ]
    out = lda_topics_batch(docs, n_topics=2)
    assert out.get("ok") is True
    assert len(out.get("topics") or []) >= 1
