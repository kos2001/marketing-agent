# marketing-agent

영업/마케팅 현황진단·타임라인·Action Items를 생성하는 multi-agent 하네스.
`weekly-report-harness`의 아키텍처(독립 재도출 검증, 축자 인용 그라운딩, 반박
검증 기반 타임라인 연속성)를 영업/마케팅 도메인에 적용했다. 설계 배경은
`docs/superpowers/specs/2026-08-11-marketing-agent-design.md`,
구현 계획은 `docs/superpowers/plans/2026-08-11-marketing-agent-mvp.md` 참고.

## 빠른 시작

```sh
scripts/setup.sh
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8001 &
cd frontend && npm run dev
```

화면: http://localhost:3001 · API: http://localhost:8001/docs

`backend/.env`의 `MA_LLM_BASE_URL`/`MA_LLM_API_KEY`/`MA_LLM_MODEL`을 채우기
전에는 `/pipeline/run`이 LLM 호출에서 실패한다 — `/sources`, `/cycles`,
`/health` 등 나머지 라우트는 LLM 없이도 동작한다.

## 아키텍처

원문 업로드 → 정규화 → 병렬 진단(D1 현황진단 ∥ D2 기회·리스크 ∥ D3 Critical
Point ∥ V·V2 독립 교차검증) → 타임라인 연속성(T1, 반박 검증) → Action Items +
총평(V3 사실검증) → 리포트.

에이전트 그래프는 `backend/app/orchestrator.py`의 `AGENT_CATALOG`에 `needs`로
선언되어 있고, 실행이 그 선언을 지키는지 `backend/tests/test_orchestrator.py`가
검사한다.

| 에이전트 | 관점 | needs |
|---|---|---|
| D1 현황진단관 | 채널·캠페인별 강점/약점 | () |
| D2 기회·리스크 정리관 | Top 기회/리스크 | () |
| D3 Critical Point 도출관 | 임팩트×시급성 | () |
| V 진단 교차검증관 | D1 독립 재탐지 | () |
| V2 기회·리스크 교차검증관 | D2 누락 점검 | () |
| T1 타임라인 정합관 | 회차를 넘는 연속성(+반박 검증) | D1, V, D2, D3 |
| Action Items 생성관 | 담당·기한·우선순위 부여 | D1, D2, D3, T1 |
| V3 총평 사실검증관 | 총평 문장별 근거 대조 | D1, D2, D3, V, V2, T1 |

## 정확도 규율

- 모든 진단/기회/리스크/Critical Point 항목은 서술과 별개로 축자 인용을 내고,
  원문과 프로그램적으로 대조해 실재하지 않는 인용만 제거한다(`app/grounding.py`).
- V·V2는 D1·D2 결과를 모른 채 원문만으로 독립 재도출한다.
- T1이 이은 타임라인 항목은 "실은 다른 사안"이라는 반박을 통과해야 유지된다.
- 판단 불가능한 경우는 "없음"이 아니라 "판단근거없음"으로 구분 표기한다.

## 테스트

```sh
cd backend && .venv/bin/pytest -v
cd frontend && npm test
```

모든 에이전트/파이프라인 테스트는 실제 LLM 호출 없이 `tests/stub_client.py`의
`StubChatClient`로 동작한다 — 실 LLM 연동은 `MA_LLM_BASE_URL`(hermes-gateway
등 OpenAI 호환 엔드포인트)로 `backend/.env`에서 설정한다.

## 디렉터리 구조

```
backend/app/
  schemas.py           # 도메인 모델 (Pydantic)
  llm.py                # ChatClient 프로토콜 + HTTP 구현 + JSON 추출
  grounding.py           # 축자 인용 대조
  storage.py              # SQLite 저장소
  agents_diagnosis.py      # D1/D2/D3, V, V2
  agents_timeline.py        # T1 (반박 검증 포함)
  agents_actions.py          # Action Items, V3
  orchestrator.py              # AGENT_CATALOG + run_pipeline
  main.py                       # FastAPI 라우트
frontend/
  lib/api.ts             # 타입 + API 클라이언트
  components/             # UploadForm, ReportView
  app/page.tsx              # 대시보드
```

## 2차 확장 후보 (이번 범위 아님)

- CRM/GA4 API 연동
- 자기개선 품질 루프(판정 상수화·침묵 감지·근거 활용률 감시)
- MCP 서버 마운트 (Claude Code에서 직접 조회)
