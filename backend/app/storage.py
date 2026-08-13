from __future__ import annotations
import sqlite3
from .schemas import SourceDoc, CycleReport


class Store:
    def __init__(self, path: str):
        # check_same_thread=False: FastAPI runs sync path operations in a
        # threadpool, so the connection created at startup is used from
        # multiple worker threads. Writes are already serialized by the
        # single connection + GIL; no concurrent-write handling needed here.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS sources ("
            "id TEXT PRIMARY KEY, cycle_id TEXT, title TEXT, text TEXT, "
            "source_type TEXT NOT NULL DEFAULT 'manual')"
        )
        # 기존 DB(마이그레이션 전)에 만든 sources 테이블에는 이 컬럼이 없다 —
        # 새 컬럼을 조건부로 추가해 예전 볼륨을 쓰는 배포에서도 깨지지 않게 한다.
        existing_cols = {row[1] for row in self._conn.execute("PRAGMA table_info(sources)")}
        if "source_type" not in existing_cols:
            self._conn.execute(
                "ALTER TABLE sources ADD COLUMN source_type TEXT NOT NULL DEFAULT 'manual'"
            )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS reports ("
            "cycle_id TEXT PRIMARY KEY, seq INTEGER, data TEXT)"
        )
        # BM25 어휘 검색 — SQLite 내장 FTS5(추가 의존성 없음). id/cycle_id는
        # UNINDEXED로 저장만 하고(필터링용), title/text만 전문 색인한다.
        # external-content 모드 대신 독립 테이블로 둬서 add_source의 갱신
        # 로직을 단순하게 유지한다(삭제 후 재삽입).
        self._conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts USING fts5("
            "id UNINDEXED, cycle_id UNINDEXED, title, text)"
        )
        # 의미 임베딩 벡터 — app/embeddings.py가 활성화됐을 때만 채워진다
        # (기본 비활성: BM25만으로도 항상 동작해야 한다).
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS source_embeddings (id TEXT PRIMARY KEY, vector BLOB)"
        )
        self._conn.commit()

    def add_source(self, doc: SourceDoc) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sources (id, cycle_id, title, text, source_type) VALUES (?, ?, ?, ?, ?)",
            (doc.id, doc.cycle_id, doc.title, doc.text, doc.source_type),
        )
        self._conn.execute("DELETE FROM sources_fts WHERE id = ?", (doc.id,))
        self._conn.execute(
            "INSERT INTO sources_fts (id, cycle_id, title, text) VALUES (?, ?, ?, ?)",
            (doc.id, doc.cycle_id, doc.title, doc.text),
        )
        self._conn.commit()

    def sources_for_cycle(self, cycle_id: str) -> list[SourceDoc]:
        rows = self._conn.execute(
            "SELECT id, cycle_id, title, text, source_type FROM sources WHERE cycle_id = ?", (cycle_id,)
        ).fetchall()
        return [SourceDoc(id=r[0], cycle_id=r[1], title=r[2], text=r[3], source_type=r[4]) for r in rows]

    def get_source(self, source_id: str) -> SourceDoc | None:
        row = self._conn.execute(
            "SELECT id, cycle_id, title, text, source_type FROM sources WHERE id = ?", (source_id,)
        ).fetchone()
        return SourceDoc(id=row[0], cycle_id=row[1], title=row[2], text=row[3], source_type=row[4]) if row else None

    def all_sources(self) -> list[SourceDoc]:
        rows = self._conn.execute(
            "SELECT id, cycle_id, title, text, source_type FROM sources"
        ).fetchall()
        return [SourceDoc(id=r[0], cycle_id=r[1], title=r[2], text=r[3], source_type=r[4]) for r in rows]

    def bm25_search(self, query: str, *, cycle_id: str | None = None, limit: int = 10) -> list[tuple[str, float]]:
        """FTS5 BM25 어휘 검색. (source_id, bm25 원점수) 목록을 관련도순으로
        반환한다 — SQLite bm25()는 값이 작을수록(더 음수일수록) 더 관련 있다."""
        match = _fts_match_expr(query)
        if not match:
            return []
        if cycle_id:
            rows = self._conn.execute(
                "SELECT id, bm25(sources_fts) AS rank FROM sources_fts "
                "WHERE sources_fts MATCH ? AND cycle_id = ? ORDER BY rank LIMIT ?",
                (match, cycle_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, bm25(sources_fts) AS rank FROM sources_fts "
                "WHERE sources_fts MATCH ? ORDER BY rank LIMIT ?",
                (match, limit),
            ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def set_embedding(self, source_id: str, vector: bytes) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO source_embeddings (id, vector) VALUES (?, ?)",
            (source_id, vector),
        )
        self._conn.commit()

    def get_embedding(self, source_id: str) -> bytes | None:
        row = self._conn.execute(
            "SELECT vector FROM source_embeddings WHERE id = ?", (source_id,)
        ).fetchone()
        return row[0] if row else None

    def all_embeddings(self, *, cycle_id: str | None = None) -> list[tuple[str, bytes]]:
        if cycle_id:
            rows = self._conn.execute(
                "SELECT e.id, e.vector FROM source_embeddings e "
                "JOIN sources s ON s.id = e.id WHERE s.cycle_id = ?",
                (cycle_id,),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT id, vector FROM source_embeddings").fetchall()
        return [(r[0], r[1]) for r in rows]

    def save_report(self, report: CycleReport) -> None:
        seq_row = self._conn.execute("SELECT COALESCE(MAX(seq), 0) FROM reports").fetchone()
        existing = self._conn.execute(
            "SELECT seq FROM reports WHERE cycle_id = ?", (report.cycle_id,)
        ).fetchone()
        seq = existing[0] if existing else seq_row[0] + 1
        self._conn.execute(
            "INSERT OR REPLACE INTO reports (cycle_id, seq, data) VALUES (?, ?, ?)",
            (report.cycle_id, seq, report.model_dump_json()),
        )
        self._conn.commit()

    def get_report(self, cycle_id: str) -> CycleReport | None:
        row = self._conn.execute(
            "SELECT data FROM reports WHERE cycle_id = ?", (cycle_id,)
        ).fetchone()
        return CycleReport.model_validate_json(row[0]) if row else None

    def list_cycles(self) -> list[str]:
        rows = self._conn.execute("SELECT cycle_id FROM reports ORDER BY seq ASC").fetchall()
        return [r[0] for r in rows]

    def prior_cycles(self, cycle_id: str) -> list[str]:
        row = self._conn.execute(
            "SELECT seq FROM reports WHERE cycle_id = ?", (cycle_id,)
        ).fetchone()
        if not row:
            return [c for c in self.list_cycles() if c != cycle_id]
        rows = self._conn.execute(
            "SELECT cycle_id FROM reports WHERE seq < ? ORDER BY seq ASC", (row[0],)
        ).fetchall()
        return [r[0] for r in rows]


def _fts_match_expr(query: str) -> str:
    """자유 텍스트 질의를 FTS5 MATCH 표현식으로 안전하게 바꾼다.

    사용자가 AND/OR/NOT, 따옴표, 괄호 같은 FTS5 문법 문자를 그대로 치면 구문
    오류가 난다. 토큰을 각각 큰따옴표로 감싸 리터럴 취급한다.

    접두(prefix, `*`) 매칭을 쓰는 이유: FTS5의 기본 unicode61 토크나이저는
    형태소 분석을 하지 않아 "오픈율"(질의)이 "오픈율이"(조사가 붙은 원문
    토큰)와 정확히 일치하지 않으면 매칭되지 않는다. 한국어 조사·어미는
    어간 뒤에 붙는 접미사이므로, 질의 토큰을 접두로 매칭하면("오픈율"*)
    "오픈율이"·"오픈율은" 같은 변형을 잡을 수 있다 — mi-report의
    `_fts_match`(backend/app/collection.py)와 동일한 처리.

    토큰은 OR로 묶어 재현율을 우선한다 — 순위는 bm25가 정한다.
    """
    import re

    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    if not tokens:
        return ""
    return " OR ".join(f'"{t}"*' for t in tokens)
