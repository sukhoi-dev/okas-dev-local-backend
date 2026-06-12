import os
import pymysql
import pymysql.cursors
from contextlib import contextmanager

# ── SQLAlchemy ORM session (FastAPI Depends) ──────────────────────────────────
from app.models.base import SessionLocal


def get_orm_session():
    """
    FastAPI dependency — yields a SQLAlchemy Session with auto-commit and
    auto-rollback.  Use as:  db: Session = Depends(get_orm_session)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

_DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "127.0.0.1"),
    "port":     int(os.getenv("DB_PORT", "3307")),
    "user":     os.getenv("DB_USER", "okasdev"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "okascloud"),
    "charset":  "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}


@contextmanager
def get_db():
    conn = pymysql.connect(**_DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
