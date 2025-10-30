from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional, Protocol, runtime_checkable

import time
from api.services.logging_config import get_logger
from api.services.metrics import record_engine_metrics
from lunt.logging import LogEvt, log_event


logger = get_logger(__name__)


@dataclass(frozen=True)
class PricingContext:
    fecha: date
    ubicacion_codigo: str
    insumos: List[Dict]
    porcentaje_indirectos: Decimal
    porcentaje_utilidad: Decimal
    output_scale_decimals: int
    allow_missing_prices: bool
    meta: Dict


@dataclass(frozen=True)
class PricingBreakdown:
    costo_directo: Decimal
    indirectos_pct: Decimal
    indirectos_monto: Decimal
    subtotal_cd_i: Decimal
    utilidad_pct: Decimal
    utilidad_monto: Decimal
    costo_total: Decimal
    warnings: List[str]
    errors: List[str]


@dataclass(frozen=True)
class PricingResult:
    breakdown: PricingBreakdown
    meta: Dict


@runtime_checkable
class BasePricingStrategy(Protocol):
    name: str

    def calcular_precio(self, ctx: PricingContext) -> PricingResult:  # pragma: no cover - interface only
        ...


def _quantize(value: Decimal, scale: int) -> Decimal:
    q = Decimal(10) ** -scale
    return value.quantize(q, rounding=ROUND_HALF_UP)


class DefaultPricingStrategy:
    name = "default"

    def calcular_precio(self, ctx: PricingContext) -> PricingResult:
        # Política de moneda: omitir monedas distintas a la mayoritaria y advertir (compat con p1.3)
        currencies = [i.get("moneda") for i in ctx.insumos if i.get("moneda") is not None]
        main_currency: Optional[str] = None
        if currencies:
            # Mayoritaria
            counts: Dict[str, int] = {}
            for c in currencies:
                counts[c] = counts.get(c, 0) + 1
            main_currency = max(counts.items(), key=lambda x: x[1])[0]

        moneda_warnings: List[str] = []
        if main_currency and any(
            (i.get("moneda") is not None and i.get("moneda") != main_currency) for i in ctx.insumos
        ):
            moneda_warnings.append(
                "MONEDA_INCONSISTENTE: se omitieron insumos de moneda distinta a la mayoritaria"
            )

        missing_prices = 0
        costo_directo = Decimal("0")
        log_event(
            logger,
            LogEvt.PRICES,
            "DEBUG",
            correlation_id=ctx.meta.get("correlation_id"),
            variant_scope=ctx.meta.get("used_variant_id") or ("multiple" if ctx.meta.get("used_variant_id") is None else None),
            items=[
                {
                    "insumo_codigo": i.get("insumo_codigo"),
                    "cantidad": float(i.get("cantidad")),
                    "unidad": i.get("unidad"),
                    "precio_unitario": (float(i.get("precio_unitario")) if i.get("precio_unitario") is not None else None),
                    "moneda": i.get("moneda"),
                    "warnings": i.get("warnings", []),
                }
                for i in ctx.insumos
            ],
        )

        for i in ctx.insumos:
            precio = i.get("precio_unitario")
            moneda = i.get("moneda")
            if precio is None:
                missing_prices += 1
                continue
            if main_currency and moneda and moneda != main_currency:
                # omitir por inconsistencia de moneda
                continue
            qty = Decimal(str(i.get("cantidad")))
            costo_directo += Decimal(str(precio)) * qty

        # Si en estricto faltan precios, abortar
        errors: List[str] = []
        warnings: List[str] = list(ctx.meta.get("warnings", []))
        if missing_prices > 0 and not ctx.allow_missing_prices:
            # Generar mensaje genérico de costo parcial bloqueado
            msg = "Faltan precios para uno o más insumos"
            errors.append(msg)
            log_event(
                logger,
                LogEvt.ERROR,
                "ERROR",
                correlation_id=ctx.meta.get("correlation_id"),
                code="PRECIO_FALTANTE",
                message=msg,
                context={"allow_missing_prices": ctx.allow_missing_prices},
            )

        if missing_prices > 0 and ctx.allow_missing_prices:
            warnings.append("COSTO_PARCIAL: insumos sin precio no se incluyen en costo_directo")
            log_event(
                logger,
                LogEvt.WARNING,
                "WARNING",
                correlation_id=ctx.meta.get("correlation_id"),
                code="COSTO_PARCIAL",
                message="Insumos sin precio considerados como costo 0",
            )

        warnings.extend(moneda_warnings)

        # Redondeos
        costo_directo = _quantize(costo_directo, 4)
        log_event(
            logger,
            LogEvt.BREAKDOWN_STEP,
            "DEBUG",
            correlation_id=ctx.meta.get("correlation_id"),
            step="costo_directo",
            value=float(costo_directo),
            accumulators={
                "costo_directo": float(costo_directo),
                "indirectos_monto": 0,
                "subtotal_cd_i": 0,
                "utilidad_monto": 0,
                "costo_total": 0,
            },
        )
        indirectos_monto = _quantize(costo_directo * ctx.porcentaje_indirectos, 4)
        log_event(
            logger,
            LogEvt.BREAKDOWN_STEP,
            "DEBUG",
            correlation_id=ctx.meta.get("correlation_id"),
            step="indirectos_monto",
            value=float(indirectos_monto),
            accumulators={
                "costo_directo": float(costo_directo),
                "indirectos_monto": float(indirectos_monto),
                "subtotal_cd_i": 0,
                "utilidad_monto": 0,
                "costo_total": 0,
            },
        )
        subtotal_cd_i = _quantize(costo_directo + indirectos_monto, 4)
        log_event(
            logger,
            LogEvt.BREAKDOWN_STEP,
            "DEBUG",
            correlation_id=ctx.meta.get("correlation_id"),
            step="subtotal_cd_i",
            value=float(subtotal_cd_i),
            accumulators={
                "costo_directo": float(costo_directo),
                "indirectos_monto": float(indirectos_monto),
                "subtotal_cd_i": float(subtotal_cd_i),
                "utilidad_monto": 0,
                "costo_total": 0,
            },
        )
        utilidad_monto = _quantize(subtotal_cd_i * ctx.porcentaje_utilidad, 4)
        log_event(
            logger,
            LogEvt.BREAKDOWN_STEP,
            "DEBUG",
            correlation_id=ctx.meta.get("correlation_id"),
            step="utilidad_monto",
            value=float(utilidad_monto),
            accumulators={
                "costo_directo": float(costo_directo),
                "indirectos_monto": float(indirectos_monto),
                "subtotal_cd_i": float(subtotal_cd_i),
                "utilidad_monto": float(utilidad_monto),
                "costo_total": 0,
            },
        )
        costo_total = _quantize(subtotal_cd_i + utilidad_monto, 4)

        # Formateo de salida
        fmt = lambda v: _quantize(v, ctx.output_scale_decimals)
        bd = PricingBreakdown(
            costo_directo=fmt(costo_directo),
            indirectos_pct=_quantize(ctx.porcentaje_indirectos, 4),
            indirectos_monto=fmt(indirectos_monto),
            subtotal_cd_i=fmt(subtotal_cd_i),
            utilidad_pct=_quantize(ctx.porcentaje_utilidad, 4),
            utilidad_monto=fmt(utilidad_monto),
            costo_total=fmt(costo_total),
            warnings=warnings,
            errors=errors,
        )

        meta = dict(ctx.meta)
        meta.update(
            {
                "strategy": self.name,
                "rounding": {"internal_scale": 4, "output_scale": ctx.output_scale_decimals},
            }
        )

        return PricingResult(breakdown=bd, meta=meta)


class PricingEngine:
    def __init__(self, strategy: Optional[BasePricingStrategy] = None):
        self._strategy = strategy or DefaultPricingStrategy()

    @property
    def strategy_name(self) -> str:
        return getattr(self._strategy, "name", self._strategy.__class__.__name__)

    def compute(self, ctx: PricingContext) -> PricingResult:
        # Logging START at engine level
        log_event(
            logger,
            LogEvt.START,
            "INFO",
            correlation_id=ctx.meta.get("correlation_id"),
            fecha=ctx.fecha.isoformat(),
            ubicacion_codigo=ctx.ubicacion_codigo,
            strategy=self.strategy_name,
        )
        start = time.perf_counter()
        result = self._strategy.calcular_precio(ctx)
        elapsed = time.perf_counter() - start
        selection_mode = str(ctx.meta.get("selection_mode") or "unknown")
        record_engine_metrics(selection_mode, self.strategy_name, elapsed)
        # Final event at engine level mirrors breakdown_final
        bd = result.breakdown
        log_event(
            logger,
            LogEvt.BREAKDOWN_FINAL,
            "INFO",
            correlation_id=ctx.meta.get("correlation_id"),
            breakdown={
                "costo_directo": float(bd.costo_directo),
                "indirectos_pct": float(bd.indirectos_pct),
                "indirectos_monto": float(bd.indirectos_monto),
                "subtotal_cd_i": float(bd.subtotal_cd_i),
                "utilidad_pct": float(bd.utilidad_pct),
                "utilidad_monto": float(bd.utilidad_monto),
                "costo_total": float(bd.costo_total),
            },
            warnings_count=len(bd.warnings),
            errors_count=len(bd.errors),
        )
        return result


# Strategy registry
PRICING_STRATEGIES: dict[str, type[BasePricingStrategy]] = {
    "default": DefaultPricingStrategy,
}


def get_pricing_strategy(name: str | None) -> BasePricingStrategy:
    if not name:
        return DefaultPricingStrategy()
    cls = PRICING_STRATEGIES.get(name.lower())
    if not cls:
        raise ValueError(f"Estrategia desconocida: {name}")
    return cls()
