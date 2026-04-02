from sqlalchemy import create_engine, text, inspect
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def ensure_runtime_schema():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    with engine.begin() as conn:
        if "user_roles" in tables:
            cols = [c["name"] for c in inspector.get_columns("user_roles")]

            if "created_at" in cols:
                conn.execute(text("ALTER TABLE user_roles ALTER COLUMN created_at SET DEFAULT NOW()"))
                conn.execute(text("UPDATE user_roles SET created_at = NOW() WHERE created_at IS NULL"))

            if "updated_at" in cols:
                conn.execute(text("ALTER TABLE user_roles ALTER COLUMN updated_at SET DEFAULT NOW()"))
                conn.execute(text("UPDATE user_roles SET updated_at = NOW() WHERE updated_at IS NULL"))

            conn.execute(text("""
                INSERT INTO user_roles (user_id, role, created_at, updated_at)
                SELECT u.id,
                       CASE WHEN u.handle = 'Varaxian' THEN 'super_admin' ELSE 'user' END,
                       NOW(),
                       NOW()
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
                )
            """))
