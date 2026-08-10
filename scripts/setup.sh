#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend =="
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" -q
[ -f .env ] || cp .env.example .env
cd ..

echo "== frontend =="
cd frontend
npm install --silent
cd ..

echo "설정 완료. 실행:"
echo "  backend:  cd backend && .venv/bin/uvicorn app.main:app --reload --port 8012"
echo "  frontend: cd frontend && NEXT_PUBLIC_API_BASE=http://localhost:8012 npm run dev"
echo "  (frontend/package.json 의 dev 스크립트는 포트 3011 을 쓴다)"
