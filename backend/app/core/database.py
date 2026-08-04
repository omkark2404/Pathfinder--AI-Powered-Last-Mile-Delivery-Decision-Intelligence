import os
import duckdb
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Base declarative class for SQLAlchemy ORM models
Base = declarative_base()

# Local SQLite fallback path
sqlite_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "lastmile.db"
)
sqlite_fallback_url = f"sqlite+aiosqlite:///{sqlite_path}"

def _resolve_database_url() -> str:
    """
    Smart Database URL Resolution:
    1. If DATABASE_URL is unset/empty -> use local SQLite fallback.
    2. If DATABASE_URL starts with 'postgres://' or 'postgresql://' (e.g. Render) -> convert to 'postgresql+asyncpg://'.
    3. If DATABASE_URL points to '@db:5432' (Docker Compose host) but we are running outside Docker -> fall back to local SQLite.
    """
    raw_url = (settings.DATABASE_URL or "").strip()

    if not raw_url:
        return sqlite_fallback_url

    # Standardize Render / Heroku postgres URLs to asyncpg driver
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+asyncpg://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Detect if pointing to Docker host 'db' while running outside Docker container
    is_docker = os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER") == "true"
    if "@db:" in raw_url and not is_docker:
        print("Database Notice: Host 'db:5432' configured for Docker. Running outside Docker — falling back to local SQLite.")
        return sqlite_fallback_url

    return raw_url


db_url = _resolve_database_url()

engine_kwargs = {
    "echo": False,
    "future": True,
}

# SQLite requires check_same_thread=False for async local development.
if db_url.startswith("sqlite+aiosqlite://"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    """Dependency for obtaining an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_duckdb_connection():
    """Returns a DuckDB connection for high-performance analytical queries."""
    duckdb_path = os.path.join(settings.DATA_DIR, "analytics.duckdb")
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    return duckdb.connect(duckdb_path)

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
