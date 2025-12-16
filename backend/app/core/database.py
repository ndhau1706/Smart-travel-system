"""
Database configuration and session management
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import os

# Get absolute path to database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "smart_travel.db")

# Check if using Cloud SQL (via Unix socket on Cloud Run)
if settings.CLOUD_SQL_CONNECTION_NAME:
    # Build PostgreSQL URL for Cloud SQL via Unix socket
    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    cloud_sql_connection_name = settings.CLOUD_SQL_CONNECTION_NAME
    
    DATABASE_URL = (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}"
        f"@/{settings.DB_NAME}"
        f"?host={db_socket_dir}/{cloud_sql_connection_name}"
    )
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )
else:
    # Use SQLite with absolute path
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        future=True
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run lightweight migrations (idempotent)
    from app.core.migrations import run_migrations

    await run_migrations(engine)


async def close_db():
    """Close database connection"""
    await engine.dispose()
