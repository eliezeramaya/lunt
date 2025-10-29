import os
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.services.cache import get_cached, set_cached

DEFAULT_INDIRECT_PERCENTAGE = Decimal(os.getenv("DEFAULT_INDIRECT_PERCENTAGE", "0.15"))
DEFAULT_UTILITY_PERCENTAGE = Decimal(os.getenv("DEFAULT_UTILITY_PERCENTAGE", "0.10"))
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION_CODE", "MX-CDMX")


class PricingEngine:
    """Motor de cálculo de precios unitarios"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_price(
        self, insumo_id: int, location_code: str, calculation_date: date
    ) -> Decimal | None:
        """
        Obtiene el precio más reciente de un insumo para una ubicación y fecha
        """
        cache_key = f"price:{insumo_id}:{location_code}:{calculation_date}"
        cached = await get_cached(cache_key)
        if cached:
            return Decimal(str(cached))

        query = (
            select(InsumoPrice.price)
            .where(
                and_(
                    InsumoPrice.insumo_id == insumo_id,
                    InsumoPrice.location_code == location_code,
                    InsumoPrice.valid_from <= calculation_date,
                )
            )
            .order_by(InsumoPrice.valid_from.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        price = result.scalar_one_or_none()

        if price:
            await set_cached(cache_key, float(price), expire=3600)

        return price

    async def build_base_preview(
        self,
        concept_code: str,
        location_code: str = DEFAULT_LOCATION,
        calculation_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Genera la previsualización base de un concepto
        Calcula costo directo, indirectos y utilidad
        """
        if calculation_date is None:
            calculation_date = date.today()

        query = select(Concept).where(Concept.code == concept_code)
        result = await self.session.execute(query)
        concept = result.scalar_one_or_none()

        if not concept:
            raise ValueError(f"Concepto no encontrado: {concept_code}")

        recipes_query = (
            select(ConceptRecipe)
            .where(
                and_(
                    ConceptRecipe.concept_id == concept.id,
                    ConceptRecipe.valid_from <= calculation_date,
                )
            )
            .order_by(ConceptRecipe.valid_from.desc())
        )

        result = await self.session.execute(recipes_query)
        recipes = result.scalars().all()

        if not recipes:
            raise ValueError(f"No se encontraron recetas para el concepto: {concept_code}")

        breakdown = []
        costo_directo = Decimal("0.00")

        for recipe in recipes:
            insumo_query = select(Insumo).where(Insumo.id == recipe.insumo_id)
            result = await self.session.execute(insumo_query)
            insumo = result.scalar_one()

            price = await self.get_latest_price(insumo.id, location_code, calculation_date)

            if price is None:
                raise ValueError(
                    f"Precio no encontrado para insumo {insumo.code} "
                    f"en {location_code} para fecha {calculation_date}"
                )

            quantity = Decimal(str(recipe.quantity))
            subtotal = price * quantity

            breakdown.append(
                {
                    "insumo_code": insumo.code,
                    "insumo_description": insumo.description,
                    "unit": insumo.unit,
                    "quantity": float(quantity),
                    "price": float(price),
                    "subtotal": float(subtotal),
                }
            )

            costo_directo += subtotal

        indirectos = costo_directo * DEFAULT_INDIRECT_PERCENTAGE
        utilidad = costo_directo * DEFAULT_UTILITY_PERCENTAGE
        precio_unitario = costo_directo + indirectos + utilidad

        return {
            "concept_code": concept.code,
            "concept_description": concept.description,
            "concept_unit": concept.unit,
            "location_code": location_code,
            "calculation_date": calculation_date.isoformat(),
            "breakdown": breakdown,
            "costo_directo": float(costo_directo),
            "indirectos": float(indirectos),
            "utilidad": float(utilidad),
            "precio_unitario": float(precio_unitario),
            "indirect_percentage": float(DEFAULT_INDIRECT_PERCENTAGE),
            "utility_percentage": float(DEFAULT_UTILITY_PERCENTAGE),
        }

    async def recalculate_with_adjustments(
        self,
        base_preview: dict[str, Any],
        adjustments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Recalcula un precio con ajustes aplicados
        Permite modificar cantidades, precios y porcentajes
        """
        breakdown = base_preview["breakdown"].copy()

        if "insumo_adjustments" in adjustments:
            for adj in adjustments["insumo_adjustments"]:
                insumo_code = adj["insumo_code"]
                for item in breakdown:
                    if item["insumo_code"] == insumo_code:
                        if "quantity" in adj:
                            item["quantity"] = adj["quantity"]
                        if "price" in adj:
                            item["price"] = adj["price"]
                        item["subtotal"] = item["quantity"] * item["price"]

        costo_directo = Decimal(str(sum(item["subtotal"] for item in breakdown)))

        indirect_pct = Decimal(
            str(adjustments.get("indirect_percentage", base_preview["indirect_percentage"]))
        )
        utility_pct = Decimal(
            str(adjustments.get("utility_percentage", base_preview["utility_percentage"]))
        )

        indirectos = costo_directo * indirect_pct
        utilidad = costo_directo * utility_pct
        precio_unitario = costo_directo + indirectos + utilidad

        return {
            **base_preview,
            "breakdown": breakdown,
            "costo_directo": float(costo_directo),
            "indirectos": float(indirectos),
            "utilidad": float(utilidad),
            "precio_unitario": float(precio_unitario),
            "indirect_percentage": float(indirect_pct),
            "utility_percentage": float(utility_pct),
        }
