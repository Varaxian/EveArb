from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

DATABASE_URL = normalize_database_url(settings.database_url)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def ensure_runtime_schema() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        if "region_market_snapshots" in existing_tables:
            columns = {col["name"] for col in inspector.get_columns("region_market_snapshots")}
            if "best_sell_location_id" not in columns:
                conn.execute(text("ALTER TABLE region_market_snapshots ADD COLUMN best_sell_location_id BIGINT"))
            if "best_buy_location_id" not in columns:
                conn.execute(text("ALTER TABLE region_market_snapshots ADD COLUMN best_buy_location_id BIGINT"))

        if "user_roles" in existing_tables:
            role_columns = {col["name"] for col in inspector.get_columns("user_roles")}
            if "created_at" in role_columns:
                conn.execute(text("ALTER TABLE user_roles ALTER COLUMN created_at SET DEFAULT NOW()"))
                conn.execute(text("UPDATE user_roles SET created_at = NOW() WHERE created_at IS NULL"))
            if "updated_at" in role_columns:
                conn.execute(text("ALTER TABLE user_roles ALTER COLUMN updated_at SET DEFAULT NOW()"))
                conn.execute(text("UPDATE user_roles SET updated_at = NOW() WHERE updated_at IS NULL"))

            insert_columns = ["user_id", "role"]
            select_columns = ["u.id", "CASE WHEN u.handle = 'Varaxian' THEN 'super_admin' ELSE 'user' END"]
            if "created_at" in role_columns:
                insert_columns.append("created_at")
                select_columns.append("NOW()")
            if "updated_at" in role_columns:
                insert_columns.append("updated_at")
                select_columns.append("NOW()")
            conn.execute(text(f"""
                INSERT INTO user_roles ({', '.join(insert_columns)})
                SELECT {', '.join(select_columns)}
                FROM users u
                WHERE NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id)
            """))

            conn.execute(text("""
                UPDATE user_roles ur
                SET role = 'super_admin', updated_at = NOW()
                FROM users u
                WHERE ur.user_id = u.id AND u.handle = 'Varaxian' AND ur.role <> 'super_admin'
            """))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
