# PostgreSQL Migration Guide

This document describes how to migrate from SQLite to PostgreSQL for production deployments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Database Setup](#database-setup)
4. [Alembic Migrations](#alembic-migrations)
5. [Data Migration](#data-migration)

---

## Prerequisites

- PostgreSQL 14+ installed and running
- Python 3.11+
- All dependencies installed: `pip install -r requirements.txt`

## Configuration

### Environment Variables

Add to your `.env.production`:

```env
# PostgreSQL Configuration
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/food_chatbot

# Individual connection params (alternative)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=food_chatbot_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=food_chatbot
```

### Docker Compose PostgreSQL Service

Already configured in `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-food_chatbot}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-food_chatbot}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-food_chatbot}"]
```

## Database Setup

### 1. Start PostgreSQL

```bash
# Using Docker
docker-compose up -d postgres

# Or use existing PostgreSQL installation
sudo systemctl start postgresql
```

### 2. Create Database and User

```sql
-- Connect as superuser
psql -U postgres

-- Create user
CREATE USER food_chatbot_user WITH PASSWORD 'your_secure_password';

-- Create database
CREATE DATABASE food_chatbot OWNER food_chatbot_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE food_chatbot TO food_chatbot_user;

-- Exit
\q
```

### 3. Test Connection

```bash
psql -U food_chatbot_user -d food_chatbot -h localhost
```

## Alembic Migrations

### Initial Setup

```bash
# Install Alembic (already in requirements.txt)
pip install alembic asyncpg

# Initialize Alembic
alembic init alembic
```

### Configuration

Edit `alembic.ini`:

```ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname

# Use environment variable
sqlalchemy.url = %(DATABASE_URL)s
```

Edit `alembic/env.py`:

```python
import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Load environment
load_dotenv()

# Import your models
from database.models import Base

# Get database URL
config = context.config
config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))

target_metadata = Base.metadata
```

### Create Initial Migration

```bash
# Generate migration from models
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Migration Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Add user preferences table"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Show current revision
alembic current

# Show migration history
alembic history
```

## Data Migration

### From SQLite to PostgreSQL

```python
# scripts/migrate_sqlite_to_postgres.py
import asyncio
import aiosqlite
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def migrate_data():
    # Connect to SQLite
    sqlite_conn = await aiosqlite.connect('data/chatbot.db')
    
    # Connect to PostgreSQL
    pg_conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Migrate users
        async with sqlite_conn.execute('SELECT * FROM users') as cursor:
            users = await cursor.fetchall()
            for user in users:
                await pg_conn.execute('''
                    INSERT INTO users (id, username, email, password_hash, role, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO NOTHING
                ''', *user)
        
        # Migrate sessions
        async with sqlite_conn.execute('SELECT * FROM sessions') as cursor:
            sessions = await cursor.fetchall()
            for session in sessions:
                await pg_conn.execute('''
                    INSERT INTO sessions (id, user_id, title, language, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO NOTHING
                ''', *session)
        
        # Migrate messages
        async with sqlite_conn.execute('SELECT * FROM messages') as cursor:
            messages = await cursor.fetchall()
            for msg in messages:
                await pg_conn.execute('''
                    INSERT INTO messages (id, session_id, role, content, timestamp, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO NOTHING
                ''', *msg)
        
        # Migrate feedback
        async with sqlite_conn.execute('SELECT * FROM feedback') as cursor:
            feedback = await cursor.fetchall()
            for fb in feedback:
                await pg_conn.execute('''
                    INSERT INTO feedback (id, session_id, user_id, rating, comment, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO NOTHING
                ''', *fb)
        
        print("✅ Migration completed successfully!")
        
    finally:
        await sqlite_conn.close()
        await pg_conn.close()

if __name__ == '__main__':
    asyncio.run(migrate_data())
```

Run migration:
```bash
python scripts/migrate_sqlite_to_postgres.py
```

## Schema Reference

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

### Sessions Table

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    language VARCHAR(10) DEFAULT 'vi',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
```

### Messages Table

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
```

### Feedback Table

```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    message_id UUID,
    restaurant_id VARCHAR(50),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    feedback_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_session_id ON feedback(session_id);
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);
```

## Production Recommendations

### Connection Pooling

Use PgBouncer for connection pooling:

```yaml
# docker-compose.yml
services:
  pgbouncer:
    image: edoburu/pgbouncer:latest
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/food_chatbot
      POOL_MODE: session
      MAX_CLIENT_CONN: 100
      DEFAULT_POOL_SIZE: 20
    ports:
      - "6432:6432"
```

### Backup Strategy

```bash
# Daily backup cron job
0 2 * * * pg_dump -U food_chatbot_user food_chatbot | gzip > /backups/food_chatbot_$(date +\%Y\%m\%d).sql.gz

# Restore from backup
gunzip -c backup.sql.gz | psql -U food_chatbot_user food_chatbot
```

### Monitoring

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

---

*Note: SQLite is sufficient for small to medium deployments. Consider PostgreSQL for:*
- *More than 1000 concurrent users*
- *Requirement for complex queries*
- *Need for horizontal scaling*
- *Production deployments with high availability requirements*
