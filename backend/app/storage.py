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
        self._conn.commit()

    def add_source(self, doc: SourceDoc) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sources (id, cycle_id, title, text, source_type) VALUES (?, ?, ?, ?, ?)",
            (doc.id, doc.cycle_id, doc.title, doc.text, doc.source_type),
        )
        self._conn.commit()

    def sources_for_cycle(self, cycle_id: str) -> list[SourceDoc]:
        rows = self._conn.execute(
            "SELECT id, cycle_id, title, text, source_type FROM sources WHERE cycle_id = ?", (cycle_id,)
        ).fetchall()
        return [SourceDoc(id=r[0], cycle_id=r[1], title=r[2], text=r[3], source_type=r[4]) for r in rows]

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
