import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    if _is_sqlite:
        path = settings.DATABASE_URL.replace("sqlite:///", "", 1)
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
    from app.models import scenario, watchlist  # noqa: F401

    Base.metadata.create_all(bind=engine)
