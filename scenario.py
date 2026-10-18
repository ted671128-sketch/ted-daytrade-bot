from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(50), default="")
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    close: Mapped[float] = mapped_column(Float)
    breakout: Mapped[float] = mapped_column(Float)
    support: Mapped[float] = mapped_column(Float)
    stop: Mapped[float] = mapped_column(Float)
    target1: Mapped[float] = mapped_column(Float)
    target2: Mapped[float] = mapped_column(Float)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
