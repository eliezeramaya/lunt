from datetime import date
from typing import Any, Dict, List

from pydantic import ValidationError


def validate_breakdown(breakdown: List[Dict[str, Any]]) -> bool:
    """
    Valida que el desglose tenga estructura correcta
    """
    required_fields = {"insumo_code", "insumo_description", "unit", "quantity", "price", "subtotal"}

    for item in breakdown:
        if not all(field in item for field in required_fields):
            raise ValueError(f"Item de desglose inválido: {item}")

        if item["quantity"] <= 0:
            raise ValueError(f"Cantidad debe ser positiva: {item['quantity']}")

        if item["price"] < 0:
            raise ValueError(f"Precio no puede ser negativo: {item['price']}")

    return True


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Valida que el rango de fechas sea correcto
    """
    if start_date > end_date:
        raise ValueError(f"Fecha inicial {start_date} es posterior a fecha final {end_date}")
    return True


def validate_percentage(value: float, field_name: str = "percentage") -> bool:
    """
    Valida que el porcentaje esté en rango válido
    """
    if not 0 <= value <= 1:
        raise ValueError(f"{field_name} debe estar entre 0 y 1, recibido: {value}")
    return True


def sanitize_concept_code(code: str) -> str:
    """
    Limpia y normaliza código de concepto
    """
    return code.strip().upper()


def sanitize_location_code(code: str) -> str:
    """
    Limpia y normaliza código de ubicación
    """
    return code.strip().upper()
