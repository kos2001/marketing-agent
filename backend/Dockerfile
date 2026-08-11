# marketing-agent 백엔드 — FastAPI + SQLite.
#
# pyproject.toml에 [build-system]이 없다(로컬 개발은 uvicorn을 backend/ 에서
# 실행해 cwd 기준으로 app 패키지를 찾는다 — 설치가 필요 없다). 그래서 Docker도
# `pip install .`로 프로젝트를 설치하는 대신, 런타임 의존성만 pip로 설치하고
# app/ 소스는 그대로 복사해 같은 방식으로 실행한다.

# ── 빌드 단계: 의존성만 먼저 설치해 앱 코드 변경 시에도 이 레이어를 캐시한다 ──
FROM python:3.12-slim AS deps
RUN pip install --no-cache-dir --target=/opt/deps \
    "fastapi[standard]>=0.110" "uvicorn[standard]>=0.29" "pydantic>=2.6" "httpx>=0.27"

# ── 런타임 단계 ────────────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install --no-install-recommends -y tini curl \
    && rm -rf /var/lib/apt/lists/*

# 루트로 돌리지 않는다. data 디렉터리(SQLite 파일)를 미리 만들고 소유권을
# 넘긴다 — 컨테이너가 비루트로 시작한 뒤에는 chown할 수 없다.
RUN useradd --create-home --uid 10001 agent \
    && mkdir -p /app/data \
    && chown -R agent:agent /app

WORKDIR /app
COPY --from=deps /opt/deps /usr/local/lib/python3.12/site-packages
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MA_DB_PATH=/app/data/marketing_agent.db

COPY --chown=agent:agent app ./app

USER agent
EXPOSE 8012

# /health가 인증 없이 항상 응답하는 라우트다.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8012/health > /dev/null || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
# python -m uvicorn: pip install --target= doesn't reliably put the uvicorn
# console-script on PATH, but the module is always importable this way.
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8012"]
