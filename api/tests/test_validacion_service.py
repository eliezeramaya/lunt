from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location
from api.schemas.validacion import ValidacionParametros
from api.services.validacion_insumos_precios import validar_insumos_y_precios


@pytest.mark.asyncio
async def test_receta_sin_insumos_stricto(db_session):
    # Datos: ubicación válida, concepto sin recetas
    db_session.add(Location(code="CDMX", name="Ciudad de México"))
    db_session.add(Concept(code="REC-002", description="Sin insumos", unit="m2"))
    await db_session.commit()

    params = ValidacionParametros(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", receta_codigos=["REC-002"]
    )
    res = await validar_insumos_y_precios(params, db_session)

    assert res.ok is False
    assert res.recetas == []
    assert any("no contiene insumos" in e for e in res.errors)


@pytest.mark.asyncio
async def test_receta_sin_insumos_tolerante(db_session):
    db_session.add(Location(code="CDMX", name="Ciudad de México"))
    db_session.add(Concept(code="REC-002", description="Sin insumos", unit="m2"))
    await db_session.commit()

    params = ValidacionParametros(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", receta_codigos=["REC-002"], allow_missing_prices=True
    )
    res = await validar_insumos_y_precios(params, db_session)

    assert res.ok is True
    assert len(res.recetas) == 1
    assert res.recetas[0].insumos == []
    assert any("no contiene insumos" in w for w in res.recetas[0].warnings)


@pytest.mark.asyncio
async def test_precio_vigente_anterior(db_session):
    # Configurar ubicación, insumo, concepto y recetas
    db_session.add(Location(code="CDMX", name="Ciudad de México"))
    conc = Concept(code="REC-001", description="Receta", unit="m2")
    ins = Insumo(code="CEM-001", description="Cemento", unit="t", category="material")
    db_session.add_all([conc, ins])
    await db_session.flush()
    db_session.add(ConceptRecipe(concept_id=conc.id, insumo_id=ins.id, quantity=1.0, valid_from=date(2024, 1, 1)))
    # Precios: sin precio exacto, pero con anterior válido
    db_session.add(
        InsumoPrice(
            insumo_id=ins.id,
            location_code="CDMX",
            price=Decimal("200.00"),
            currency="MXN",
            valid_from=date(2025, 8, 15),
        )
    )
    await db_session.commit()

    params = ValidacionParametros(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", receta_codigos=["REC-001"]
    )
    res = await validar_insumos_y_precios(params, db_session)

    assert res.ok is True
    assert len(res.recetas) == 1
    assert res.recetas[0].insumos[0].precio_unitario == Decimal("200.00")


@pytest.mark.asyncio
async def test_varios_precios_toma_mas_reciente(db_session):
    db_session.add(Location(code="CDMX", name="Ciudad de México"))
    conc = Concept(code="REC-001", description="Receta", unit="m2")
    ins = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    db_session.add_all([conc, ins])
    await db_session.flush()
    db_session.add(ConceptRecipe(concept_id=conc.id, insumo_id=ins.id, quantity=0.5, valid_from=date(2024, 1, 1)))
    # Tres precios previos, debe elegir el de 2025-08-28
    db_session.add_all(
        [
            InsumoPrice(
                insumo_id=ins.id,
                location_code="CDMX",
                price=Decimal("150.00"),
                currency="MXN",
                valid_from=date(2025, 6, 1),
            ),
            InsumoPrice(
                insumo_id=ins.id,
                location_code="CDMX",
                price=Decimal("190.00"),
                currency="MXN",
                valid_from=date(2025, 7, 1),
            ),
            InsumoPrice(
                insumo_id=ins.id,
                location_code="CDMX",
                price=Decimal("250.00"),
                currency="MXN",
                valid_from=date(2025, 8, 28),
            ),
        ]
    )
    await db_session.commit()

    params = ValidacionParametros(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", receta_codigos=["REC-001"]
    )
    res = await validar_insumos_y_precios(params, db_session)
    assert res.ok is True
    assert res.recetas[0].insumos[0].precio_unitario == Decimal("250.00")


@pytest.mark.asyncio
async def test_ubicacion_inexistente_error(db_session):
    # No crear Location
    params = ValidacionParametros(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", receta_codigos=["REC-001"]
    )
    res = await validar_insumos_y_precios(params, db_session)
    assert res.ok is False
    assert any("Ubicación inválida" in e for e in res.errors)


@pytest.mark.asyncio
async def test_cantidad_invalida(db_session):
    db_session.add(Location(code="CDMX", name="Ciudad de México"))
    conc = Concept(code="REC-001", description="Receta", unit="m2")
    ins = Insumo(code="CEM-001", description="Cemento", unit="t", category="material")
    db_session.add_all([conc, ins])
    await db_session.flush()
    # Cantidad 0 -> inválida
    db_session.add(ConceptRecipe(concept_id=conc.id, insumo_id=ins.id, quantity=0.0, valid_from=date(2024, 1, 1)))
    await db_session.commit()

    params = ValidacionParametros(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", receta_codigos=["REC-001"]
    )
    res = await validar_insumos_y_precios(params, db_session)
    assert res.ok is False
    assert any("Cantidad inválida" in e for e in res.errors)


@pytest.mark.asyncio
async def test_tolerante_mezcla_precios(db_session):
    db_session.add(Location(code="CDMX", name="Ciudad de México"))
    conc = Concept(code="REC-001", description="Receta", unit="m2")
    ins1 = Insumo(code="CEM-001", description="Cemento", unit="t", category="material")
    ins2 = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    db_session.add_all([conc, ins1, ins2])
    await db_session.flush()
    db_session.add_all(
        [
            ConceptRecipe(concept_id=conc.id, insumo_id=ins1.id, quantity=1.0, valid_from=date(2024, 1, 1)),
            ConceptRecipe(concept_id=conc.id, insumo_id=ins2.id, quantity=0.5, valid_from=date(2024, 1, 1)),
        ]
    )
    # Solo ARE-020 tiene precio
    db_session.add(
        InsumoPrice(
            insumo_id=ins2.id,
            location_code="CDMX",
            price=Decimal("250.00"),
            currency="MXN",
            valid_from=date(2025, 8, 1),
        )
    )
    await db_session.commit()

    params = ValidacionParametros(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", receta_codigos=["REC-001"], allow_missing_prices=True
    )
    res = await validar_insumos_y_precios(params, db_session)

    assert res.ok is True
    assert res.errors == []
    assert len(res.recetas) == 1
    insumos = res.recetas[0].insumos
    cem = next(i for i in insumos if i.insumo_codigo == "CEM-001")
    are = next(i for i in insumos if i.insumo_codigo == "ARE-020")
    assert cem.precio_unitario is None and cem.moneda is None
    assert are.precio_unitario == Decimal("250.00") and are.moneda == "MXN"
    assert any("sin precio" in w for w in res.recetas[0].warnings)

