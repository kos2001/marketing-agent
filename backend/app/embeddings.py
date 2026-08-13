"""로컬 의미 임베딩(fastembed) — 하이브리드(BM25+벡터) 검색용.

~/gitspace/mi-report/backend/app/embeddings.py를 그대로 옮겼다. fastembed
(ONNX, 로컬)로 텍스트를 임베딩해 외부 API 호출·데이터 유출 없이 의미 검색을
낸다. 미설치이거나 MA_EMBEDDINGS로 켜지 않았으면 available()=False가 되어
app/search.py가 BM25 단독 검색으로 조용히 폴백한다 — 기본 설치에는
fastembed가 없다(이미지 크기·설치 시간 때문에 opt-in: extras=embeddings).
"""
from __future__ import annotations

import os
import struct
import threading

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_embedder = None
_unavailable = False
_lock = threading.Lock()


def enabled() -> bool:
    """환경변수로 임베딩 기능을 켰는지(기본 꺼짐)."""
    return os.environ.get("MA_EMBEDDINGS", "").strip().lower() in ("1", "true", "yes", "on")


def model_name() -> str:
    return os.environ.get("MA_EMBED_MODEL", "").strip() or DEFAULT_MODEL


def _get():
    """로컬 임베더 싱글턴(최초 호출 시 모델 로드/다운로드). 실패 시 None."""
    global _embedder, _unavailable
    if _embedder is not None:
        return _embedder
    if _unavailable:
        return None
    with _lock:
        if _embedder is not None:
            return _embedder
        try:
            from fastembed import TextEmbedding

            _embedder = TextEmbedding(model_name=model_name())
            return _embedder
        except Exception:
            _unavailable = True
            return None


def available() -> bool:
    """fastembed가 실제로 로드 가능한지(설치 여부 + 모델 로드 성공)."""
    return enabled() and _get() is not None


def embed(texts: list[str]) -> list[list[float]] | None:
    """텍스트 목록을 임베딩한다. 비활성/미설치/실패면 None(호출부가 BM25로 폴백)."""
    if not enabled():
        return None
    model = _get()
    if model is None:
        return None
    try:
        return [list(v) for v in model.embed(texts)]
    except Exception:
        return None


def vector_to_bytes(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def bytes_to_vector(data: bytes) -> list[float]:
    n = len(data) // 4
    return list(struct.unpack(f"{n}f", data))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def reset() -> None:
    """테스트 전용 — 싱글턴 상태를 초기화한다."""
    global _embedder, _unavailable
    _embedder = None
    _unavailable = False
