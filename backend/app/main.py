from __future__ import annotations
import os
import uuid
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Settings
from .storage import Store
from .llm import ChatClient, HttpChatClient
from .schemas import SourceDoc, SourceType, CycleReport
from .orchestrator import run_pipeline
from .demo_fixture import seed_demo_data
from .doctext import extract_text, UnsupportedDocumentError, SUPPORTED_EXTENSIONS

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB — 텍스트 문서 기준으로 충분히 넉넉한 상한

app = FastAPI(title="marketing-agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_settings = Settings.from_env()
os.makedirs(os.path.dirname(_settings.db_path) or ".", exist_ok=True)
_store = Store(_settings.db_path)
_client = HttpChatClient(
    _settings.llm_base_url, _settings.llm_api_key, _settings.llm_model, timeout_s=_settings.llm_timeout_s
)
if _settings.seed_demo_data:
    seed_demo_data(_store)


def get_store() -> Store:
    return _store


def get_client() -> ChatClient:
    return _client


class SourceIn(BaseModel):
    cycle_id: str
    title: str
    text: str
    source_type: SourceType = "manual"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/source-types")
def source_types():
    """어떤 종류의 소스를 태깅할 수 있는지 프런트가 조회하는 라우트."""
    from typing import get_args
    return list(get_args(SourceType))


@app.post("/sources")
def add_source(payload: SourceIn, store: Store = Depends(get_store)):
    doc = SourceDoc(
        id=f"s-{uuid.uuid4().hex[:8]}", cycle_id=payload.cycle_id, title=payload.title, text=payload.text,
        source_type=payload.source_type,
    )
    store.add_source(doc)
    return {"id": doc.id}


@app.get("/upload-formats")
def upload_formats():
    return list(SUPPORTED_EXTENSIONS)


@app.post("/sources/upload")
async def upload_source(
    cycle_id: str = Form(...),
    source_type: SourceType = Form("upload"),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    store: Store = Depends(get_store),
):
    """PDF/DOCX/TXT/MD 문서를 업로드해 텍스트를 추출하고 소스로 저장한다."""
    filename = file.filename or "업로드 문서"
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다 (최대 10MB)")
    try:
        text = extract_text(filename, content)
    except UnsupportedDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not text.strip():
        raise HTTPException(status_code=422, detail="문서에서 텍스트를 추출하지 못했습니다")

    doc = SourceDoc(
        id=f"s-{uuid.uuid4().hex[:8]}", cycle_id=cycle_id, title=title or filename, text=text,
        source_type=source_type,
    )
    store.add_source(doc)
    return {"id": doc.id, "extracted_chars": len(text)}


@app.get("/sources/{cycle_id}", response_model=list[SourceDoc])
def get_sources(cycle_id: str, store: Store = Depends(get_store)):
    return store.sources_for_cycle(cycle_id)


@app.post("/pipeline/run", response_model=CycleReport)
async def run(cycle_id: str, store: Store = Depends(get_store), client: ChatClient = Depends(get_client)):
    return await run_pipeline(client, store, cycle_id)


@app.get("/reports/{cycle_id}", response_model=CycleReport)
def get_report(cycle_id: str, store: Store = Depends(get_store)):
    report = store.get_report(cycle_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report


@app.get("/cycles")
def list_cycles(store: Store = Depends(get_store)):
    return store.list_cycles()
