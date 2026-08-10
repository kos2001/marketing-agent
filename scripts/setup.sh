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
echo "  backend:  cd backend && .venv/bin/uvicorn app.main:app --reload --port 8001"
echo "  frontend: cd frontend && npm run dev"
