# marketing-agent

영업/마케팅 현황진단·타임라인·Action Items를 생성하는 multi-agent 하네스.
`weekly-report-harness`의 아키텍처(독립 재도출 검증, 축자 인용 그라운딩, 반박
검증 기반 타임라인 연속성)를 영업/마케팅 도메인에 적용했다. 설계 배경은
`docs/superpowers/specs/2026-08-11-marketing-agent-design.md`,
구현 계획은 `docs/superpowers/plans/2026-08-11-marketing-agent-mvp.md` 참고.

## 빠른 시작

### Docker (권장)

```sh
cp backend/.env.example backend/.env   # scripts/setup_hermes_profile.sh --apply 로 채운다
hermes -p marketing-agent gateway restart   # 호스트에서 LLM api_server 기동 (:8654)
docker compose up -d --build
```

화면: http://localhost:3011 · API: http://localhost:8012/docs

백엔드 컨테이너는 `host.docker.internal`로 호스트의 hermes api_server에
접속한다(`docker-compose.yml`이 `MA_LLM_BASE_URL`을 덮어쓴다) — 컨테이너 안의
`127.0.0.1`은 컨테이너 자신이라 `.env`의 값 그대로는 닿지 않는다.

`NEXT_PUBLIC_API_BASE`를 바꿨으면(포트 등) `docker compose up -d --build`로
**다시 빌드**해야 한다 — Next.js가 이 값을 빌드 시점에 클라이언트 번들에
문자열로 박아 넣으므로, 이미지 태그가 같으면 캐시된 이전 빌드가 그대로
재사용되어 조용히 낡은 값을 서빙한다(실제로 이 문제로 한 번 8013이 박힌 채
돌았던 것을 잡아냈다 — 매번 `--build`를 붙이는 습관이 안전하다).

### 로컬 (Docker 없이)

```sh
scripts/setup.sh
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8012 &
cd frontend && NEXT_PUBLIC_API_BASE=http://localhost:8012 npm run dev
```

화면: http://localhost:3011 · API: http://localhost:8012/docs

> 포트는 8012/3011을 쓴다(기본 8001/3001이 아니다) — 이 머신에서
> `weekly-report-harness`의 Docker 컨테이너가 이미 8001·3001을 점유하고 있어
> 충돌한다. 다른 머신에서 그 충돌이 없다면 원하는 포트로 자유롭게 바꿔도 된다;
> 프런트는 `NEXT_PUBLIC_API_BASE`로, 백엔드는 `uvicorn --port`로 지정한다.

`backend/.env`의 `MA_LLM_BASE_URL`/`MA_LLM_API_KEY`/`MA_LLM_MODEL`을 채우기
전에는 `/pipeline/run`이 LLM 호출에서 실패한다 — `/sources`, `/cycles`,
`/health` 등 나머지 라우트는 LLM 없이도 동작한다.

### LLM 연동 — hermes-agent `marketing-agent` 프로파일

이 저장소는 `weekly-report-harness`와 같은 방식으로 전용 hermes-agent 프로파일을
쓴다. LLM 호출은 hermes-gateway를 거치지 않고 hermes-agent의 api_server에
직접 붙는다(1차 범위 — gateway 경유는 다중 인스턴스가 필요해지면 추가).

```sh
scripts/setup_hermes_profile.sh          # dry-run 으로 작업 확인
scripts/setup_hermes_profile.sh --apply  # marketing-agent 프로파일 생성 (:8654)
hermes -p marketing-agent gateway restart
curl -s http://127.0.0.1:8654/health
```

프로파일의 인격·정확도 규율은 `backend/profiles/marketing-agent/SOUL.md`에
있다(독립 재도출·축자 인용·판단 보류 표기 등 이 저장소의 정확도 규율을 그대로
반영). `hermes -p marketing-agent config set model.default <model>` 로 모델을
지정해야 한다(프로파일 생성 직후에는 비어 있다). 마지막으로
`backend/.env`에 다음을 채운다:

```
MA_LLM_BASE_URL=http://127.0.0.1:8654/v1
MA_LLM_API_KEY=<setup_hermes_profile.sh 가 생성한 API_SERVER_KEY>
MA_LLM_MODEL=marketing-agent
```

실측(2026-08-11): 이메일/인스타그램/법인 고객(ACME, Beta Corp) 성과 텍스트로
`/pipeline/run`을 실행해 아래 10개 에이전트 전체가 축자 인용과 함께 정상
생성됨을 확인했다 — 지어낸 고객명 없이 원문에 있는 두 법인만 식별했고,
전략의 3축은 정확히 3개, Action Items는 즉시 확인 4건 → 조치 필요 3건 →
최종 요약 순으로 나왔다.

### 데모 데이터

저장소가 비어 있으면(회차가 하나도 없으면) 백엔드가 시작할 때
`backend/app/demo_fixture.py`의 정적 데모 리포트(`demo-2026-W30`)를 LLM
호출 없이 채워 넣는다 — 클론하자마자 빈 화면이 아니라 실제 리포트 구조를
바로 볼 수 있다. 프런트엔드도 이 회차를 기본값으로 두고 마운트 시 한 번
자동으로 불러온다. 값은 이 프로젝트를 실 hermes api_server로 검증했을 때
나온 산출물의 패턴을 그대로 따른다(현황진단·지표 대시보드·고객별 대응
전략·전략의 3축·Action Items 전 구간).

실 리포트가 하나라도 저장되면(`/pipeline/run`을 한 번이라도 완주하면) 다음
재시작부터는 데모 데이터를 다시 채우지 않는다 — 판정 기준은 저장된 리포트의
존재 여부다(`Store.list_cycles()`). `MA_SEED_DEMO_DATA=0`으로 완전히 끌 수도
있다.

## 아키텍처

원문 업로드 → 정규화 → 병렬 진단(D1 현황진단 ∥ D2 기회·리스크 ∥ D3 Critical
Point ∥ V·V2 독립 교차검증) → 타임라인 연속성(T1, 반박 검증) → 종합(SUMMARY·
STRATEGY·ACTIONS·V3 총평 병렬) → 리포트.

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
| SUMMARY 현황진단 종합관 | Executive Summary·고객별 대응 전략·법인 대응 process | D1, D2, D3 |
| STRATEGY 전략/타임라인 수립관 | 사안별 전략 가이드·전략의 3축·권장 타임라인 | D1, D2, D3, T1 |
| ACTIONS 실행 전환관 | 즉시 확인 → 조치 필요 → 최종 요약 | D1, D2, D3, T1 |
| V3 총평 사실검증관 | 총평 문장별 근거 대조 | D1, D2, D3, V, V2, T1 |

### 리포트 구성

- **현황진단**: Executive Summary, **지표 대시보드**(측정→관리→개선), 채널별
  진단, 고객(법인)별 대응 전략, 법인 대응 process
- **전략/타임라인**: 사안별 전략 가이드, 전략의 3축(정확히 3개), 권장
  타임라인(이미 반복 중인 사안일수록 이른 시점에 배치), 회차 간 연속성
- **Action Items**: 즉시 확인 → 조치 필요 → 최종 요약. 각 항목에 우선순위와
  별개로 **Impact/Effort**를 붙여 "임팩트는 크지만 하기 쉬운 것"과 "긴급하지만
  임팩트는 작은 것"을 구분한다.

### 외부 플러그인 저장소 조사 반영 (2026-08-11)

`anthropics/knowledge-work-plugins`(marketing/performance-report,
sales/pipeline-review), `modu-ai/moai-cowork`(marketing-performance-report,
data-provenance-auditor), `panaversity/agentfactory-business-plugins`
(sales-revops-marketing/pipeline)를 조사해 두 가지를 적용했다:

- **지표 대시보드** (`DiagnosisSummary.metrics`, SUMMARY 에이전트) —
  performance-report류 스킬의 "지표/이전값/변화/목표/상태" 테이블 패턴. 단,
  이 저장소의 그라운딩 규율을 지키기 위해 **원문에 없는 지표나 외부 시장
  평균치는 만들어 넣지 않는다**고 프롬프트에 명시했다 — moai 쪽 스킬의 문서에
  나온 "2025년 평균 전환율 1.99%" 같은 시장 벤치마크는 우리 파이프라인의
  인용 대상이 아니므로 가져오지 않았다.
- **Impact/Effort 매트릭스** (`ActionItem.impact`/`.effort`) —
  performance-report의 2×2 우선순위 매트릭스, pipeline-review의 딜 우선순위
  로직에서 가져온 개념. priority(긴급도)와 별개 축으로 둬 두 판단을 섞지
  않는다.

검토했지만 이번에는 적용하지 않은 것(향후 후보로 `2차 확장 후보`에 기록):
`ai-slop-reviewer`류 서술 다듬기 후처리 패스, eval 골든셋 기반 회귀 테스트
하네스(agentfactory-business-plugins의 `evals/` 패턴), 결정적 규칙 기반 리스크
플래깅(예: "14일 이상 무활동 = 위험" — 우리는 이미 `repeat_count`로 일부
구현했고, 나머지는 LLM 판단에 맡기는 현재 방식이 검증에서 잘 작동해 우선순위가
낮다).

### github.com/topics/sales 조사 반영 (2026-08-11)

토픽 상위 결과 대부분은 PHP/Java 등 다른 스택의 CRM·ERP·POS 전체 플랫폼이라
코드 이식은 맞지 않았다. 그 중 B2B 영업 전용 Claude Skills 저장소 두 개
(`keinsaasforever/gtm-pipeline-skills`, `Othmane-Khadri/gtm-engineer-playbook`)
에서 개념 하나를 가져왔다:

- **계정 리스크 티어** (`CustomerStrategy.risk_level`: stable/at_risk/critical)
  — gtm-engineer-playbook의 Qualification Scorer가 쓰는 리드 온도 티어링
  (HOT/WARM/COLD/PARK)을, 신규 리드 발굴이 아니라 **이미 확보한 법인 계정의
  건강도**를 빠르게 훑는 용도로 바꿔 적용했다. 실측: 불만을 제기하며 계약
  재검토를 언급한 고객은 `critical`, 특별한 이슈 없이 정상 이용 중이라고 밝힌
  고객은 `stable`로 정확히 갈렸다.

두 저장소가 중심으로 다루는 리드 발굴·enrichment·ICP 스코어링(company-search,
signal-search, people-search 등)은 이 프로젝트의 범위(기존 성과 진단)와
맞지 않아 가져오지 않았다 — 이 하네스는 잠재 고객을 찾는 도구가 아니라
이미 확보한 채널·고객의 현황을 진단하는 도구다.

### 프론트엔드 기술 스택

Next.js 15(App Router) + React 19 + Tailwind v4 위에 다음을 얹었다:

- **TanStack Query v5** — `app/page.tsx`가 리포트 조회/실행을 `useQuery`/
  `useMutation`으로 다룬다. 캐시 키는 `["report", cycleId]` — 회차를 바꾸면
  자동으로 새 쿼리가 된다.
- **Zod** — `lib/schemas.ts`가 `backend/app/schemas.py`와 1:1 대응하는 스키마를
  정의하고, `lib/api.ts`가 모든 응답을 `.parse()`로 검증한다. 백엔드 모양이
  바뀌었는데 프론트가 조용히 깨지는 것(런타임에야 드러나는 `undefined` 접근)을
  막는다 — 실제로 이 세션에서만 `CycleReport` 모양이 세 번 바뀌었다. 실 백엔드
  응답으로 스키마 정합성을 검증했다(`ZOD VALIDATION: PASS`).
- **next/font (Geist Sans/Mono)** — `weekly-report-harness`와 동일한 폰트
  최적화. Geist는 라틴 문자만 지원하므로 한글은 자동으로 폴백 스택
  (Apple SD Gothic Neo 등)으로 넘어간다 — harness와 동일한 동작이다.

타입은 `lib/schemas.ts`의 zod 스키마에서 `z.infer`로 도출한다 — 수동으로 쓴
TS interface와 실제 검증 로직이 따로 노는 문제가 없다.

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
  agents_summary.py          # SUMMARY (현황진단 종합: Executive Summary 등)
  agents_strategy.py          # STRATEGY (전략/타임라인: 전략의 3축 등)
  agents_actions.py            # ACTIONS (Action Items), V3 (총평 사실검증)
  orchestrator.py                # AGENT_CATALOG + run_pipeline
  demo_fixture.py                 # 빈 저장소용 데모 리포트 (LLM 호출 없음)
  main.py                          # FastAPI 라우트
frontend/
  lib/schemas.ts          # zod 스키마 (백엔드 schemas.py와 1:1 대응) + 타입
  lib/api.ts               # API 클라이언트 (zod로 응답 검증)
  lib/query-provider.tsx     # TanStack QueryClientProvider
  lib/cycle-context.tsx       # 페이지 간 공유하는 "지금 보는 회차" 상태
  lib/use-report.ts            # 회차의 리포트를 조회하는 공유 훅
  components/                   # UploadForm, CyclePicker, report-sections.tsx, ui.tsx
  app/icon.tsx                   # 파비콘 (next/og ImageResponse)
  app/apple-icon.tsx               # Apple 터치 아이콘
  app/page.tsx                      # 대시보드
  app/sources/page.tsx                # 수집 자료
  app/diagnosis/page.tsx                # 현황진단
  app/strategy/page.tsx                   # 전략/타임라인
  app/actions/page.tsx                      # Action Items
  app/history/page.tsx                        # 회차 히스토리
  app/manual/page.tsx                           # 사용 안내
docker-compose.yml    # backend + frontend 2개 서비스, SQLite는 볼륨 하나
backend/Dockerfile    # 멀티스테이지: 의존성 레이어 → 런타임 (tini + 비루트)
frontend/Dockerfile   # 멀티스테이지: standalone 빌드 → 최소 런타임
```

### 프론트엔드 페이지 구조 — mi-report 반영

`~/gitspace/mi-report`(사내 시장정보 리포트 하네스)는 대시보드 하나에 모든
걸 몰아넣지 않고, 사이드바로 데이터 수집·주제별·다이제스트·경쟁사·리포트·
히스토리·매뉴얼을 각각의 페이지로 나눈다. 이 프로젝트도 원래 페이지 하나에
전체 리포트를 스크롤하는 구조였는데, 그 페이지 조직 패턴을 옮겨 7개 라우트로
나눴다:

| 라우트 | mi-report의 대응 페이지 | 내용 |
|---|---|---|
| `/` | 대시보드 | 회차 선택, 자료 업로드, 파이프라인 실행, 총평 |
| `/sources` | 수집 결과/수집 문서 | 이 회차에 올라온 원문(소스 종류 태그와 함께) |
| `/diagnosis` | 주간 리포트(의 일부) | 현황진단 전 구간 |
| `/strategy` | 주제별 History(의 일부) | 전략/타임라인 전 구간 |
| `/actions` | 주간 리포트(의 일부) | Action Items 전 구간 |
| `/history` | 생성물 이력 | 지금까지 생성된 모든 회차 목록 |
| `/manual` | 사용 안내 | 사용 순서 안내 |

mi-report에는 있지만 옮기지 않은 페이지: 뉴스 다이제스트·경쟁사 IR·문서
Q&A·스케줄·VOC — 각각 뉴스 스크래핑·재무공시 연동·RAG 코퍼스·크론·VoC
전용 워크플로가 필요해 이 프로젝트의 범위(사용자가 붙여넣은 텍스트를 그
자리에서 진단) 밖이다. `customer_feedback` 소스 타입이 VoC 개념을 가볍게
대신한다.

페이지 간에는 `CycleProvider`(React Context)로 "지금 보는 회차"를 공유한다
— 사이드바 이동은 `next/link`(클라이언트 사이드 라우팅)로 하므로 페이지를
옮겨도 회차 선택이 유지된다. 각 페이지의 `useReport()`는 TanStack Query의
같은 `["report", cycleId]` 캐시 키를 쓰므로, 같은 회차라면 페이지를 옮겨도
다시 fetch하지 않는다.

## 2차 확장 후보 (이번 범위 아님)

- CRM/GA4 API 연동
- 자기개선 품질 루프(판정 상수화·침묵 감지·근거 활용률 감시)
- MCP 서버 마운트 (Claude Code에서 직접 조회)
- 서술 필드(총평·Executive Summary) AI 티 제거 후처리 패스
  (moai-cowork의 `ai-slop-reviewer` → `korean-humanize` 체인 참고)
- eval 골든셋 기반 회귀 테스트 (agentfactory-business-plugins의 `evals/` 패턴 참고
  — 지금은 StubChatClient 기반 결정적 테스트만 있고, 실 LLM 출력 품질을 추적하는
  골든셋은 없다)
