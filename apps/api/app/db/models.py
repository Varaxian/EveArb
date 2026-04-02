from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(50), default="user", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)



class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EveCharacter(Base):
    __tablename__ = "eve_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    character_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    character_name: Mapped[str] = mapped_column(String(255), index=True)
    client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    character_owner_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    token_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EveAuthToken(Base):
    __tablename__ = "eve_auth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    eve_character_id: Mapped[int] = mapped_column(Integer, index=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scope_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_preference_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UniverseSystem(Base):
    __tablename__ = "universe_systems"

    system_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    security_status: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UniverseSystemLink(Base):
    __tablename__ = "universe_system_links"

    __table_args__ = (
        UniqueConstraint("from_system_id", "to_system_id", name="uq_system_link"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_system_id: Mapped[int] = mapped_column(Integer, index=True)
    to_system_id: Mapped[int] = mapped_column(Integer, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TypeMetadata(Base):
    __tablename__ = "type_metadata"

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class LocationNameCache(Base):
    __tablename__ = "location_name_cache"

    location_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_kind: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RegionMarketSnapshot(Base):
    __tablename__ = "region_market_snapshots"

    __table_args__ = (
        UniqueConstraint("snapshot_at", "region_id", "type_id", name="uq_snapshot_region_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=utcnow)
    region_id: Mapped[int] = mapped_column(Integer, index=True)
    type_id: Mapped[int] = mapped_column(Integer, index=True)
    best_sell: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_buy: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_volume: Mapped[int] = mapped_column(Integer, default=0)
    buy_volume: Mapped[int] = mapped_column(Integer, default=0)
    best_sell_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    best_buy_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_name: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserOpportunity(Base):
    __tablename__ = "user_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    type_id: Mapped[int] = mapped_column(Integer, index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    src_region_id: Mapped[int] = mapped_column(Integer, index=True)
    dst_region_id: Mapped[int] = mapped_column(Integer, index=True)
    buy_price: Mapped[float] = mapped_column(Float)
    sell_price: Mapped[float] = mapped_column(Float)
    buy_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    buy_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sell_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    sell_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_profit_per_unit: Mapped[float] = mapped_column(Float)
    expected_net_profit_isk: Mapped[float] = mapped_column(Float)
    roi: Mapped[float] = mapped_column(Float, default=0.0)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_jumps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route_security_profile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    fail_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CompletedOpportunity(Base):
    __tablename__ = "completed_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    source_opportunity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    type_id: Mapped[int] = mapped_column(Integer, index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    src_region_id: Mapped[int] = mapped_column(Integer, index=True)
    dst_region_id: Mapped[int] = mapped_column(Integer, index=True)
    buy_price: Mapped[float] = mapped_column(Float)
    sell_price: Mapped[float] = mapped_column(Float)
    buy_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    buy_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sell_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    sell_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_profit_per_unit: Mapped[float] = mapped_column(Float)
    expected_net_profit_isk: Mapped[float] = mapped_column(Float)
    roi: Mapped[float] = mapped_column(Float, default=0.0)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_jumps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route_security_profile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class FailedOpportunity(Base):
    __tablename__ = "failed_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    source_opportunity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    type_id: Mapped[int] = mapped_column(Integer, index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    src_region_id: Mapped[int] = mapped_column(Integer, index=True)
    dst_region_id: Mapped[int] = mapped_column(Integer, index=True)
    buy_price: Mapped[float] = mapped_column(Float)
    sell_price: Mapped[float] = mapped_column(Float)
    buy_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    buy_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sell_location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    sell_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_profit_per_unit: Mapped[float] = mapped_column(Float)
    expected_net_profit_isk: Mapped[float] = mapped_column(Float)
    roi: Mapped[float] = mapped_column(Float, default=0.0)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_jumps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route_security_profile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fail_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
