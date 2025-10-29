from datetime import date

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Concept(Base, TimestampMixin):
    """
    Conceptos de obra: actividades o elementos constructivos
    Ej: Excavacion, Muro de block, Losa de concreto
    """

    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Embeddings para búsqueda semántica (placeholder)
    embedding_vector: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    recipes: Mapped[list["ConceptRecipe"]] = relationship(
        "ConceptRecipe", back_populates="concept", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_concepts_description_gin", "description", postgresql_using="gin"),)

    def __repr__(self) -> str:
        return f"<Concept(code={self.code}, description={self.description[:30]})>"


class ConceptRecipe(Base, TimestampMixin):
    """
    Receta de un concepto: lista de insumos con cantidades
    Un concepto puede tener múltiples versiones de receta
    """

    __tablename__ = "concept_recipes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    insumo_id: Mapped[int] = mapped_column(ForeignKey("insumos.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(nullable=False)
    valid_from: Mapped[date] = mapped_column(nullable=False)
    valid_until: Mapped[date | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    concept: Mapped["Concept"] = relationship("Concept", back_populates="recipes")
    insumo: Mapped["Insumo"] = relationship("Insumo", back_populates="recipes")

    __table_args__ = (
        Index("ix_concept_recipes_concept_valid", "concept_id", "valid_from", "valid_until"),
        Index("ix_concept_recipes_insumo", "insumo_id"),
    )

    def __repr__(self) -> str:
        return f"<ConceptRecipe(concept_id={self.concept_id}, insumo_id={self.insumo_id}, qty={self.quantity})>"
