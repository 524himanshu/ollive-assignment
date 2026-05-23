from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.core.config import settings


def get_engine():
    if settings.USE_SQLITE:
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
        )
        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        return engine
    else:
        return create_engine(
            settings.DATABASE_URL,
            pool_size=10,
            max_overflow=20,
        )


engine = get_engine()

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False
)


class Base(DeclarativeBase):
    pass


def init_db():
    import app.models.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()