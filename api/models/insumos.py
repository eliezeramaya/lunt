from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Insumo(Base, TimestampMixin):
    """
    Insumos: materiales, mano de obra, equipo, herramientas
    Ej: Cemento gris CPC 30R, Oficial albanil, Revolvedora
    """

    __tablename__ = "insumos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    prices: Mapped[list["InsumoPrice"]] = relationship(
        "InsumoPrice", back_populates="insumo", cascade="all, delete-orphan"
    )
    recipes: Mapped[list["ConceptRecipe"]] = relationship("ConceptRecipe", back_populates="insumo")

    __table_args__ = (Index("ix_insumos_category", "category"),)

    def __repr__(self) -> str:
        return f"<Insumo(code={self.code}, description={self.description[:30]})>"


class InsumoPrice(Base, TimestampMixin):
    """
    Precios históricos de insumos por ubicación y fecha
    Append-only: nunca se actualizan, solo se insertan nuevas versiones
    """

    __tablename__ = "insumo_prices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    insumo_id: Mapped[int] = mapped_column(ForeignKey("insumos.id"), nullable=False)
    location_code: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="MXN", nullable=False)
    valid_from: Mapped[date] = mapped_column(nullable=False)
    valid_until: Mapped[date | None] = mapped_column(nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    insumo: Mapped["Insumo"] = relationship("Insumo", back_populates="prices")

    __table_args__ = (
        Index(
            "ix_insumo_prices_location_date",
            "insumo_id",
            "location_code",
            "valid_from",
            postgresql_ops={"valid_from": "DESC"},
        ),
        Index("ix_insumo_prices_insumo", "insumo_id"),
    )

    def __repr__(self) -> str:
        return f"<InsumoPrice(insumo_id={self.insumo_id}, location={self.location_code}, price={self.price})>"
