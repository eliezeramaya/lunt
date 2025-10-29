#!/usr/bin/env python3
"""
Script to load seed data from CSV files into database
Run after database migrations: python scripts/load_seed.py
"""

import asyncio
import csv
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice, Location, User

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://lunt_user:lunt_pass@localhost:5432/lunt_db"
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def load_locations(session: AsyncSession) -> None:
    """Load default locations"""
    locations = [
        {"code": "MX-CDMX", "name": "Ciudad de Mexico", "state": "CDMX", "country": "Mexico"},
        {"code": "MX-GDL", "name": "Guadalajara", "state": "Jalisco", "country": "Mexico"},
        {"code": "MX-MTY", "name": "Monterrey", "state": "Nuevo Leon", "country": "Mexico"},
    ]

    for loc_data in locations:
        query = select(Location).where(Location.code == loc_data["code"])
        result = await session.execute(query)
        if not result.scalar_one_or_none():
            location = Location(**loc_data)
            session.add(location)
            print(f"Loaded location: {loc_data['code']}")

    await session.commit()


async def load_users(session: AsyncSession) -> None:
    """Load default test user"""
    query = select(User).where(User.email == "admin@lunt.com")
    result = await session.execute(query)
    if not result.scalar_one_or_none():
        user = User(
            email="admin@lunt.com",
            hashed_password="$2b$12$dummy_hash_for_testing",  # TODO: Replace with real hash
            is_active=True,
            is_superuser=True,
            full_name="Admin User",
        )
        session.add(user)
        await session.commit()
        print("Loaded default admin user")


async def load_concepts(session: AsyncSession) -> None:
    """Load concepts from CSV"""
    csv_path = Path(__file__).parent.parent / "data" / "seed" / "concepts.csv"

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = select(Concept).where(Concept.code == row["code"])
            result = await session.execute(query)
            if not result.scalar_one_or_none():
                concept = Concept(
                    code=row["code"],
                    description=row["description"],
                    unit=row["unit"],
                    category=row["category"],
                )
                session.add(concept)
                print(f"Loaded concept: {row['code']}")

    await session.commit()


async def load_insumos(session: AsyncSession) -> None:
    """Load insumos from CSV"""
    csv_path = Path(__file__).parent.parent / "data" / "seed" / "insumos.csv"

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = select(Insumo).where(Insumo.code == row["code"])
            result = await session.execute(query)
            if not result.scalar_one_or_none():
                insumo = Insumo(
                    code=row["code"],
                    description=row["description"],
                    unit=row["unit"],
                    category=row["category"],
                )
                session.add(insumo)
                print(f"Loaded insumo: {row['code']}")

    await session.commit()


async def load_concept_recipes(session: AsyncSession) -> None:
    """Load concept recipes from CSV"""
    csv_path = Path(__file__).parent.parent / "data" / "seed" / "concept_recipes.csv"

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            concept_query = select(Concept).where(Concept.code == row["concept_code"])
            concept_result = await session.execute(concept_query)
            concept = concept_result.scalar_one_or_none()

            insumo_query = select(Insumo).where(Insumo.code == row["insumo_code"])
            insumo_result = await session.execute(insumo_query)
            insumo = insumo_result.scalar_one_or_none()

            if concept and insumo:
                valid_from = datetime.strptime(row["valid_from"], "%Y-%m-%d").date()

                query = select(ConceptRecipe).where(
                    ConceptRecipe.concept_id == concept.id,
                    ConceptRecipe.insumo_id == insumo.id,
                    ConceptRecipe.valid_from == valid_from,
                )
                result = await session.execute(query)
                if not result.scalar_one_or_none():
                    recipe = ConceptRecipe(
                        concept_id=concept.id,
                        insumo_id=insumo.id,
                        quantity=float(row["quantity"]),
                        valid_from=valid_from,
                    )
                    session.add(recipe)
                    print(f"Loaded recipe: {row['concept_code']} -> {row['insumo_code']}")

    await session.commit()


async def load_insumo_prices(session: AsyncSession) -> None:
    """Load insumo prices from CSV"""
    csv_path = Path(__file__).parent.parent / "data" / "seed" / "insumo_precios.csv"

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            insumo_query = select(Insumo).where(Insumo.code == row["insumo_code"])
            insumo_result = await session.execute(insumo_query)
            insumo = insumo_result.scalar_one_or_none()

            if insumo:
                valid_from = datetime.strptime(row["valid_from"], "%Y-%m-%d").date()

                query = select(InsumoPrice).where(
                    InsumoPrice.insumo_id == insumo.id,
                    InsumoPrice.location_code == row["location_code"],
                    InsumoPrice.valid_from == valid_from,
                )
                result = await session.execute(query)
                if not result.scalar_one_or_none():
                    price = InsumoPrice(
                        insumo_id=insumo.id,
                        location_code=row["location_code"],
                        price=Decimal(row["price"]),
                        currency=row["currency"],
                        valid_from=valid_from,
                    )
                    session.add(price)
                    print(f"Loaded price: {row['insumo_code']} @ {row['location_code']}")

    await session.commit()


async def main():
    """Main function to load all seed data"""
    print("Starting seed data load...")

    async with AsyncSessionLocal() as session:
        await load_locations(session)
        await load_users(session)
        await load_concepts(session)
        await load_insumos(session)
        await load_concept_recipes(session)
        await load_insumo_prices(session)

    print("Seed data loaded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
