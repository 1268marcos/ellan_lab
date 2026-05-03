"""
Análise de sentimento (positivo / neutro / negativo) e intenção em português.

Prioridade: embeddings multilingues (SentenceTransformers, compatível com PT-BR).
Fallback sem torch: TF–IDF + frases-âncora em português.
"""
from __future__ import annotations

import logging
import math
from functools import lru_cache
from typing import Any, Literal

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "neutral", "negative"]
IntentLabel = Literal["reclamacao", "elogio", "sugestao", "urgente"]

# Frases-âncora em PT-BR (cosine vs texto / vs média das âncoras por classe)
_ANCHORS_SENTIMENT: dict[SentimentLabel, list[str]] = {
    "positive": [
        "excelente atendimento adorei",
        "muito satisfeito super recomendo",
        "ótima experiência tudo certo",
        "rápido e eficiente perfeito",
    ],
    "neutral": [
        "ok dentro do esperado",
        "nem bom nem ruim comum",
        "funcionou normalmente",
        "sem grandes surpresas",
    ],
    "negative": [
        " péssimo horrível decepcionado ",
        "não recomendo problema grave",
        "atraso absurdo e falta de respeito",
        "ruim demais suporte inexistente",
    ],
}

_ANCHORS_INTENT: dict[IntentLabel, list[str]] = {
    "reclamacao": ["reclamação de problema defeito erro", "estou insatisfeito com"],
    "elogio": ["parabéns adorei elogio excelente", "muito obrigado ficou ótimo"],
    "sugestao": ["sugiro que poderiam melhorar", "seria bom se implementassem"],
    "urgente": ["urgente preciso hoje imediatamente", "emergência crítico já"],
}


@lru_cache(maxsize=1)
def _sentence_transformer_model():
    from sentence_transformers import SentenceTransformer

    name = (settings.feedback_embedding_model or "").strip() or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    logger.info("loading SentenceTransformer: %s", name)
    return SentenceTransformer(name)


def _encode_st(texts: list[str]) -> np.ndarray:
    model = _sentence_transformer_model()
    emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(emb, dtype=np.float64)


def _encode_tfidf_fit_once(corpus: list[str]) -> tuple[TfidfVectorizer, np.ndarray]:
    vec = TfidfVectorizer(
        max_features=4096,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    mat = vec.fit_transform(corpus)
    return vec, mat


def _sentiment_from_scores(pos: float, neu: float, neg: float) -> tuple[SentimentLabel, float]:
    """Mapeia logits simples (similaridade média por classe) para rótulo e score contínuo [-1,1]."""
    m = max(pos, neu, neg, 1e-9)
    if pos == m:
        return "positive", min(1.0, (pos - max(neu, neg)) / m)
    if neg == m:
        return "negative", max(-1.0, -(neg - max(neu, pos)) / m)
    return "neutral", (pos - neg) / m


def analyze_text(text: str) -> dict[str, Any]:
    """
    Retorna sentiment_label, sentiment_score (-1..1), user_intent, confidence, embedding_backend.
    """
    raw = (text or "").strip()
    if not raw:
        return {
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "user_intent": "sugestao",
            "confidence": 0.0,
            "embedding_backend": "none",
            "detail": "empty_text",
        }

    use_tfidf = bool(settings.feedback_use_tfidf_only)
    backend = "tfidf"
    pos_s = neu_s = neg_s = 0.0
    intent_scores: dict[IntentLabel, float] = {k: 0.0 for k in _ANCHORS_INTENT}

    if not use_tfidf:
        try:
            s_texts: list[str] = []
            for phrases in _ANCHORS_SENTIMENT.values():
                s_texts.extend(phrases)
            i_texts: list[str] = []
            intent_keys: list[IntentLabel] = []
            for lab, phrases in _ANCHORS_INTENT.items():
                for p in phrases:
                    i_texts.append(p)
                    intent_keys.append(lab)

            emb_doc = _encode_st([raw])[0]
            emb_s = _encode_st(s_texts)
            # média por classe de sentimento
            idx = 0
            sums = {k: [] for k in _ANCHORS_SENTIMENT}
            for lab, _ph in [(lab, ph) for lab, arr in _ANCHORS_SENTIMENT.items() for ph in arr]:
                sums[lab].append(emb_s[idx])
                idx += 1
            pos_s = float(np.mean([cosine_similarity([emb_doc], [v])[0, 0] for v in sums["positive"]]))
            neu_s = float(np.mean([cosine_similarity([emb_doc], [v])[0, 0] for v in sums["neutral"]]))
            neg_s = float(np.mean([cosine_similarity([emb_doc], [v])[0, 0] for v in sums["negative"]]))

            emb_i = _encode_st(i_texts)
            for j, lab in enumerate(intent_keys):
                sim = float(cosine_similarity([emb_doc], [emb_i[j]])[0, 0])
                intent_scores[lab] = max(intent_scores[lab], sim)

            backend = "sentence_transformers"
        except Exception:
            logger.exception("SentenceTransformer indisponível; usando TF-IDF")
            use_tfidf = True

    if use_tfidf:
        backend = "tfidf"
        corpus: list[str] = []
        sent_groups: list[tuple[SentimentLabel, str]] = []
        for lab, phrases in _ANCHORS_SENTIMENT.items():
            for p in phrases:
                corpus.append(p)
                sent_groups.append((lab, p))
        intent_flat: list[tuple[IntentLabel, str]] = []
        for lab, phrases in _ANCHORS_INTENT.items():
            for p in phrases:
                corpus.append(p)
                intent_flat.append((lab, p))
        corpus.append(raw)
        vec, mat = _encode_tfidf_fit_once(corpus)
        ix_raw = len(corpus) - 1
        v_raw = mat[ix_raw]
        pos_s = neu_s = neg_s = 0.0
        counts = {k: 0 for k in _ANCHORS_SENTIMENT}
        for i, (lab, _) in enumerate(sent_groups):
            sim = cosine_similarity(v_raw, mat[i])[0, 0]
            if lab == "positive":
                pos_s += sim
                counts["positive"] += 1
            elif lab == "neutral":
                neu_s += sim
                counts["neutral"] += 1
            else:
                neg_s += sim
                counts["negative"] += 1
        pos_s = pos_s / max(1, counts["positive"])
        neu_s = neu_s / max(1, counts["neutral"])
        neg_s = neg_s / max(1, counts["negative"])

        intent_scores = {k: 0.0 for k in _ANCHORS_INTENT}
        off = len(sent_groups)
        for j, (lab, _) in enumerate(intent_flat):
            sim = cosine_similarity(v_raw, mat[off + j])[0, 0]
            intent_scores[lab] = max(intent_scores[lab], sim)

    label, margin = _sentiment_from_scores(pos_s, neu_s, neg_s)
    # score contínuo aproximado em [-1,1]
    sentiment_score = max(-1.0, min(1.0, (pos_s - neg_s) / max(1e-6, pos_s + neu_s + neg_s)))

    best_intent = max(intent_scores, key=intent_scores.get)  # type: ignore[arg-type]
    intent_conf = float(intent_scores[best_intent])

    conf = float(max(pos_s, neu_s, neg_s))
    if math.isnan(sentiment_score):
        sentiment_score = 0.0

    return {
        "sentiment_label": label,
        "sentiment_score": sentiment_score,
        "user_intent": best_intent,
        "confidence": conf,
        "intent_confidence": intent_conf,
        "embedding_backend": backend,
        "scores": {"positive": pos_s, "neutral": neu_s, "negative": neg_s},
    }
