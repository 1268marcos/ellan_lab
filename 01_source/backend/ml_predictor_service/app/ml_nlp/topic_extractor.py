"""Extração de tópicos: palavras-chave (TF–IDF) e LDA opcional em lote."""
from __future__ import annotations

import logging
import re
from typing import Any

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

logger = logging.getLogger(__name__)

# Stopwords mínimas PT (corpus pequeno / LDA)
_PT_STOP = frozenset(
    """
    de a o que e do da em um para é com não uma os no se na por mais as dos como mas foi ao ele
    das tem à seu sua ou ser quando muito há nos já está também só pelo até isso ela entre era
    depois sem mesmo aos ter seus quem nas me esse eles estão você tinha foram essa num nem suas
    meu minha numa pelos elas qual nós lhe deles essas esses pelas este dela pelo pela muito bem
    """.split()
)


def _tokenize_words(text: str) -> list[str]:
    t = (text or "").lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    return [w for w in t.split() if len(w) > 2 and w not in _PT_STOP]


def keyword_topics(text: str, top_k: int = 8) -> list[str]:
    """Tópicos aproximados por frequência de tokens (documento único)."""
    words = _tokenize_words(text)
    if not words:
        return []
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.keys(), key=lambda w: (-freq[w], w))
    return ranked[:top_k]


def lda_topics_batch(
    documents: list[str],
    n_topics: int = 5,
    max_features: int = 200,
    top_words: int = 6,
) -> dict[str, Any]:
    """
    LDA clássico (sklearn) em vários documentos. Retorna palavras por tópico + pesos.
    Requer len(documents) >= n_topics (senão reduz n_topics).
    """
    docs = [d.strip() for d in documents if d and d.strip()]
    if len(docs) < 3:
        return {"ok": False, "reason": "need_at_least_3_documents", "topics": []}

    n_topics = max(2, min(n_topics, len(docs) - 1))
    try:
        vec = CountVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            stop_words=list(_PT_STOP),
        )
        X = vec.fit_transform(docs)
        if X.shape[1] == 0:
            return {"ok": False, "reason": "empty_vocabulary", "topics": []}
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=20,
            learning_method="online",
            random_state=42,
            n_jobs=-1,
        )
        lda.fit(X)
        names = vec.get_feature_names_out()
        out: list[dict[str, Any]] = []
        for topic_idx, topic in enumerate(lda.components_):
            top_ix = topic.argsort()[:-top_words - 1 : -1]
            words = [str(names[i]) for i in top_ix]
            out.append({"topic_id": int(topic_idx), "words": words, "weights": [float(topic[i]) for i in top_ix]})
        return {"ok": True, "n_topics": n_topics, "topics": out}
    except Exception:
        logger.exception("lda_topics_batch failed")
        return {"ok": False, "reason": "lda_error", "topics": []}


def try_bertopic_batch(documents: list[str]) -> dict[str, Any] | None:
    """BERTopic opcional (se instalado)."""
    try:
        from bertopic import BERTopic  # type: ignore[import-not-found]
    except ImportError:
        return None
    docs = [d for d in documents if d and str(d).strip()]
    if len(docs) < 5:
        return None
    try:
        topic_model = BERTopic(language="multilingual", calculate_probabilities=False, verbose=False)
        topics, _ = topic_model.fit_transform(docs)
        info = topic_model.get_topic_info()
        rows = info.head(12).to_dict(orient="records") if hasattr(info, "to_dict") else []
        return {"ok": True, "bertopic": True, "assignments": [int(x) for x in topics], "topic_info": rows}
    except Exception:
        logger.exception("bertopic failed")
        return {"ok": False, "bertopic": True, "error": "fit_failed"}
