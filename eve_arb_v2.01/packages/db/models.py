from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime
import datetime as dt

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    character_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="viewer")
    status: Mapped[str] = mapped_column(String(50), default="pending")

class LoadCurrent(Base):
    __tablename__ = "load_current"
    id: Mapped[int] = mapped_column(primary_key=True)
    type_id: Mapped[int] = mapped_column(Integer, index=True)
    item_name: Mapped[str] = mapped_column(String(255))
    buy_price_unit: Mapped[float] = mapped_column(Float)
    sell_price_unit: Mapped[float] = mapped_column(Float)
    max_qty: Mapped[int] = mapped_column(Integer)
    total_m3: Mapped[float] = mapped_column(Float)
    total_profit: Mapped[float] = mapped_column(Float)

class ListingPattern(Base):
    __tablename__ = "listing_patterns"
    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(Integer, index=True)
    type_id: Mapped[int] = mapped_column(Integer, index=True)
    recurrence_score: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
