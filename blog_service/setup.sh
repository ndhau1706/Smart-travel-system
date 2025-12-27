#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "venv" ]; then
  python -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

echo "Setup complete."
echo "Next steps:"
echo "1) alembic upgrade head"
echo "2) uvicorn main:app --reload"
