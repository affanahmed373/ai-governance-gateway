"""Pure-Python TF-IDF + logistic regression prompt-injection classifier (ADR 0012)."""

from __future__ import annotations

import itertools
import math
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import yaml

LABELS_PATH = Path(__file__).resolve().parent.parent / "config" / "prompt_injection_labels.yaml"
_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def ml_enabled() -> bool:
    raw = os.getenv("GATEWAY_INJECTION_ML") or os.getenv("gateway-injection-ml") or "1"
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def ml_threshold() -> float:
    raw = os.getenv("GATEWAY_INJECTION_ML_THRESHOLD") or os.getenv(
        "gateway-injection-ml-threshold"
    )
    if raw is None or raw.strip() == "":
        return 0.5
    return float(raw)


def reset_classifier_cache() -> None:
    """Clear the fitted model (tests that change labels or env)."""
    _fitted_model.cache_clear()


def _load_labels(path: Path = LABELS_PATH) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "train" not in data or "eval" not in data:
        raise ValueError(f"expected train and eval lists in {path}")
    return data


def _texts_and_labels(rows: list[dict]) -> tuple[list[str], list[int]]:
    texts: list[str] = []
    labels: list[int] = []
    for row in rows:
        label = row["label"]
        if label not in {"injection", "benign"}:
            raise ValueError(f"unknown label {label!r}")
        texts.append(str(row["text"]))
        labels.append(1 if label == "injection" else 0)
    return texts, labels


def _tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    unigrams = tokens
    bigrams = [f"{a}_{b}" for a, b in itertools.pairwise(tokens)]
    return unigrams + bigrams


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


class _TfidfLogReg:
    """Minimal binary classifier: TF-IDF features + L2 logistic regression."""

    def __init__(self) -> None:
        self.vocab: dict[str, int] = {}
        self.idf: list[float] = []
        self.weights: list[float] = []
        self.bias: float = 0.0

    def fit(self, texts: list[str], labels: list[int], epochs: int = 80, lr: float = 0.35) -> None:
        docs = [_tokenize(t) for t in texts]
        df: Counter[str] = Counter()
        for tokens in docs:
            df.update(set(tokens))
        terms = sorted(df)
        self.vocab = {term: i for i, term in enumerate(terms)}
        n_docs = len(docs)
        self.idf = [math.log((1 + n_docs) / (1 + df[term])) + 1.0 for term in terms]
        n_features = len(terms)
        self.weights = [0.0] * n_features
        self.bias = 0.0

        vectors = [self._vectorize_tokens(tokens) for tokens in docs]
        # Class-balanced sample weights
        n_pos = sum(labels) or 1
        n_neg = (len(labels) - sum(labels)) or 1
        sample_w = [0.5 * len(labels) / n_pos if y == 1 else 0.5 * len(labels) / n_neg for y in labels]

        for _ in range(epochs):
            for x, y, sw in zip(vectors, labels, sample_w, strict=True):
                score = self.bias + sum(self.weights[i] * v for i, v in x.items())
                pred = _sigmoid(score)
                err = (pred - y) * sw
                self.bias -= lr * err
                for i, v in x.items():
                    self.weights[i] -= lr * (err * v + 1e-4 * self.weights[i])

    def _vectorize_tokens(self, tokens: list[str]) -> dict[int, float]:
        counts = Counter(t for t in tokens if t in self.vocab)
        if not counts:
            return {}
        length = sum(counts.values())
        vec: dict[int, float] = {}
        for term, count in counts.items():
            idx = self.vocab[term]
            tf = count / length
            vec[idx] = tf * self.idf[idx]
        # L2 normalise
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {i: v / norm for i, v in vec.items()}

    def predict_proba(self, text: str) -> float:
        x = self._vectorize_tokens(_tokenize(text))
        score = self.bias + sum(self.weights[i] * v for i, v in x.items())
        return _sigmoid(score)


@lru_cache(maxsize=1)
def _fitted_model() -> _TfidfLogReg:
    data = _load_labels()
    texts, y = _texts_and_labels(data["train"])
    model = _TfidfLogReg()
    model.fit(texts, y)
    return model


def injection_score(text: str) -> float:
    """Probability that text is prompt injection (0..1)."""
    return _fitted_model().predict_proba(text)


def predict_injection(text: str, threshold: float | None = None) -> bool:
    if not ml_enabled():
        return False
    cut = ml_threshold() if threshold is None else threshold
    return injection_score(text) >= cut


def evaluate_on_eval_set(
    threshold: float | None = None,
    path: Path = LABELS_PATH,
) -> dict[str, float | int]:
    """Precision and recall of the ML score alone on the held-out eval split."""
    data = _load_labels(path)
    texts, y_true = _texts_and_labels(data["eval"])
    cut = ml_threshold() if threshold is None else threshold
    y_pred = [1 if injection_score(t) >= cut else 0 for t in texts]
    tp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 1 and yp == 1)
    fp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 1 and yp == 0)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "support": len(y_true),
        "threshold": cut,
    }
