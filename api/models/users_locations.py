from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Location(Base, TimestampMixin):
    """Ubicaciones geográficas para precios regionalizados"""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default="Mexico", nullable=False)

    def __repr__(self) -> str:
        return f"<Location(code={self.code}, name={self.name})>"


class User(Base, TimestampMixin):
    """
    Usuarios del sistema (placeholder para FastAPI Users)
    TODO: Implement full authentication with FastAPI Users
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    drafts: Mapped[list["Draft"]] = relationship("Draft", back_populates="user")
    quotes: Mapped[list["Quote"]] = relationship("Quote", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(email={self.email})>"
