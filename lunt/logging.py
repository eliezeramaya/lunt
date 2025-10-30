from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from typing import Any, Iterator
from zoneinfo import ZoneInfo


MX_TZ = ZoneInfo("America/Mexico_City")


@dataclass(frozen=True)
class LogSettings:
    log_level: str = os.getenv("LUNT_LOG_LEVEL", "INFO").upper()
    log_env: str = os.getenv("LUNT_LOG_ENV", os.getenv("ENVIRONMENT", "development"))
    log_service: str = os.getenv("LUNT_LOG_SERVICE", "lunt.pricing")
    log_version: str = os.getenv("LUNT_LOG_VERSION", os.getenv("API_VERSION", "v1"))
    debug_sampling: float = float(os.getenv("LUNT_LOG_DEBUG_SAMPLING", "1.0"))


settings = LogSettings()


class LogEvt:
    START = "pricing.start"
    VARIANTS = "pricing.variants"
    PRICES = "pricing.prices"
    BREAKDOWN_STEP = "pricing.breakdown_step"
    BREAKDOWN_FINAL = "pricing.breakdown_final"
    WARNING = "pricing.warning"
    ERROR = "pricing.error"
    END = "pricing.end"


def _should_emit_debug(correlation_id: str | None) -> bool:
    if settings.debug_sampling >= 1.0:
        return True
    if not correlation_id:
        return False
    h = sha1(correlation_id.encode("utf-8")).hexdigest()
    # Map to [0,1)
    val = int(h[:8], 16) / 0xFFFFFFFF
    return val <= settings.debug_sampling


def log_event(logger: logging.Logger, evt: str, level: str = "INFO", **payload: Any) -> None:
    level = level.upper()
    corr_id = payload.pop("correlation_id", None)
    if level == "DEBUG" and not _should_emit_debug(corr_id):
        return
    rec: dict[str, Any] = {
        "evt": evt,
        "level": level,
        "correlation_id": corr_id,
        "service": settings.log_service,
        "env": settings.log_env,
        "version": settings.log_version,
        "ts": datetime.now(MX_TZ).isoformat(),
        **payload,
    }
    line = json.dumps(rec, default=str, ensure_ascii=False)
    getattr(logger, level.lower(), logger.info)(line)


@contextmanager
def timed_section(name: str) -> Iterator[dict[str, float]]:
    start = time.perf_counter()
    data: dict[str, float] = {}
    try:
        yield data
    finally:
        end = time.perf_counter()
        data["name"] = name
        data["elapsed_ms"] = (end - start) * 1000.0

