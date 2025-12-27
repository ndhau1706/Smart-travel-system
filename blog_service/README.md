# Blog Service

## Quickstart

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Set environment:
   - `cp .env.example .env` and update `DATABASE_URL`
3. Run migrations:
   - `alembic upgrade head`
4. Start server:
   - `uvicorn main:app --reload`
