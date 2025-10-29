from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Draft(Base, TimestampMixin):
    """
    Borradores de cotizaciones en progreso
    Permite previsualizar y modificar antes de confirmar
    """

    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    concept_code: Mapped[str] = mapped_column(String(50), nullable=False)
    concept_description: Mapped[str] = mapped_column(Text, nullable=False)
    location_code: Mapped[str] = mapped_column(String(20), nullable=False)
    calculation_date: Mapped[datetime] = mapped_column(nullable=False)

    # Resultados del cálculo
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    costo_directo: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    indirectos: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    utilidad: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)

    # Parametros ajustables
    indirect_percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False
    )
    utility_percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="drafts")

    __table_args__ = (Index("ix_drafts_user_date", "user_id", "calculation_date"),)

    def __repr__(self) -> str:
        return f"<Draft(id={self.id}, concept={self.concept_code}, PU={self.precio_unitario})>"


class Quote(Base, TimestampMixin):
    """
    Cotizaciones confirmadas e inmutables
    Registro histórico de precios calculados
    """

    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts.id"), nullable=True)
    quote_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    concept_code: Mapped[str] = mapped_column(String(50), nullable=False)
    concept_description: Mapped[str] = mapped_column(Text, nullable=False)
    location_code: Mapped[str] = mapped_column(String(20), nullable=False)
    calculation_date: Mapped[datetime] = mapped_column(nullable=False)

    # Snapshot inmutable del cálculo
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    costo_directo: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    indirectos: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    utilidad: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)

    indirect_percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False
    )
    utility_percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quotes")

    __table_args__ = (
        Index("ix_quotes_user_date", "user_id", "calculation_date"),
        Index("ix_quotes_concept", "concept_code"),
    )

    def __repr__(self) -> str:
        return f"<Quote(number={self.quote_number}, concept={self.concept_code}, PU={self.precio_unitario})>"
