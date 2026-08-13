from app import embeddings


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MA_EMBEDDINGS", raising=False)
    assert embeddings.enabled() is False
    assert embeddings.available() is False
    assert embeddings.embed(["텍스트"]) is None


def test_enabled_via_env_var(monkeypatch):
    monkeypatch.setenv("MA_EMBEDDINGS", "1")
    assert embeddings.enabled() is True
    monkeypatch.setenv("MA_EMBEDDINGS", "true")
    assert embeddings.enabled() is True
    monkeypatch.setenv("MA_EMBEDDINGS", "0")
    assert embeddings.enabled() is False


def test_model_name_default_and_override(monkeypatch):
    monkeypatch.delenv("MA_EMBED_MODEL", raising=False)
    assert embeddings.model_name() == embeddings.DEFAULT_MODEL
    monkeypatch.setenv("MA_EMBED_MODEL", "custom/model")
    assert embeddings.model_name() == "custom/model"


def test_vector_bytes_roundtrip():
    vector = [0.1, -0.5, 1.25, 0.0]
    data = embeddings.vector_to_bytes(vector)
    restored = embeddings.bytes_to_vector(data)
    assert len(restored) == len(vector)
    for a, b in zip(vector, restored):
        assert abs(a - b) < 1e-6


def test_cosine_similarity_identical_vectors():
    v = [1.0, 2.0, 3.0]
    assert abs(embeddings.cosine_similarity(v, v) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal_vectors():
    assert abs(embeddings.cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_cosine_similarity_zero_vector_is_zero():
    assert embeddings.cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_embed_returns_none_when_fastembed_not_installed(monkeypatch):
    """embeddings 활성화 extras 없이 기본 설치 상태를 검증 — MA_EMBEDDINGS=1을
    켜도 fastembed가 없으면 예외 없이 None으로 우아하게 폴백해야 한다."""
    monkeypatch.setenv("MA_EMBEDDINGS", "1")
    embeddings.reset()
    result = embeddings.embed(["텍스트"])
    # CI/기본 설치에는 fastembed가 없으므로 None이 기대값이다.
    # (embeddings extras를 설치한 환경에서 돌리면 실제 벡터가 나올 수 있다 —
    # 그 경우는 available()이 True가 되어 이 assert가 자연히 건너뛰어진다.)
    if not embeddings.available():
        assert result is None
    embeddings.reset()
