from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, Integer
from uuid import uuid4, UUID as UUIDT
from datetime import datetime

class Base(DeclarativeBase):
    pass

# Table: account
class Account(Base):
    __tablename__ = "account"
    account_id: Mapped[UUIDT] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    account_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

# Table: chat_session
class ChatSession(Base):
    __tablename__ = "chat_session"
    session_id: Mapped[UUIDT] = mapped_column(primary_key=True)
    account_id: Mapped[UUIDT] = mapped_column(ForeignKey("account.account_id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

# Table: chat_message
class ChatMessage(Base):
    __tablename__ = "chat_message"
    message_id: Mapped[UUIDT] = mapped_column(primary_key=True)
    session_id: Mapped[UUIDT | None] = mapped_column(ForeignKey("chat_session.session_id", ondelete="SET NULL"))
    message_ts: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    message_role: Mapped[str] = mapped_column(String(50), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

# Table: crisis
class Crisis(Base):
    __tablename__ = "crisis"
    crisis_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crisis_name: Mapped[str] = mapped_column(Text, nullable=False)

# Table: crisis_alert
class CrisisAlert(Base):
    __tablename__ = "crisis_alert"
    crisis_alert_id: Mapped[UUIDT] = mapped_column(primary_key=True)
    account_id: Mapped[UUIDT] = mapped_column(ForeignKey("account.account_id", ondelete="CASCADE"), nullable=False)
    crisis_id: Mapped[UUIDT] = mapped_column(ForeignKey("crisis.crisis_id", ondelete="CASCADE"), nullable=False)
    crisis_alert_severity: Mapped[str] = mapped_column(Text, nullable=False)
    crisis_alert_status: Mapped[str] = mapped_column(Text, nullable=False)
    crisis_alert_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    crisis_alert_ts: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

