from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class KnowledgeChunk(Base):
    """Фрагмент документа из базы знаний с векторным эмбеддингом."""
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    source: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Эмбеддинг хранится как текст в формате '[0.1, 0.2, ...]' для совместимости
    # с pgvector через cast. При наличии pgvector используйте тип Vector(384).
    embedding: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(String(255))
    facility: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    device_numbers: Mapped[str | None] = mapped_column(Text)
    device_type: Mapped[str | None] = mapped_column(String(255))
    emotional_tone: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(100))
    issue_summary: Mapped[str | None] = mapped_column(Text)
    original_text: Mapped[str | None] = mapped_column(Text)
    ai_response: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (
        CheckConstraint("emotional_tone IN ('Позитив','Нейтрально','Негатив')", name="chk_tickets_emotional_tone"),
        CheckConstraint("status IN ('Новое','В работе','Закрыто')", name="chk_tickets_status"),
    )

    tg_binding: Mapped["TelegramTicketBinding | None"] = relationship(
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan",
    )
    events: Mapped[list["TicketEvent"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketEvent.ts",
    )


class TelegramChannel(Base):
    __tablename__ = "telegram_channels"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(255))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TelegramLinkToken(Base):
    __tablename__ = "telegram_link_tokens"

    token: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID string
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TelegramTicketBinding(Base):
    __tablename__ = "telegram_ticket_bindings"

    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    base_text: Mapped[str | None] = mapped_column(Text)

    channel_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    channel_message_id: Mapped[int | None] = mapped_column(BigInteger)

    discussion_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    discussion_root_message_id: Mapped[int | None] = mapped_column(BigInteger)

    timeline_message_id: Mapped[int | None] = mapped_column(BigInteger)

    assignee: Mapped[str | None] = mapped_column(String(255))

    ticket: Mapped["Ticket"] = relationship(back_populates="tg_binding")


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    by: Mapped[str | None] = mapped_column(String(255))
    prev: Mapped[str | None] = mapped_column(String(255))

    ticket: Mapped["Ticket"] = relationship(back_populates="events")