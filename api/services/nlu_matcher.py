from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Concept


class NLUMatcher:
    """
    Matcher de lenguaje natural para buscar conceptos
    TODO: Implementar búsqueda semántica con Qdrant
    TODO: Usar embeddings para mejorar matching
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_concept_by_description(
        self, description: str, limit: int = 5
    ) -> List[Tuple[Concept, float]]:
        """
        Busca conceptos por descripción usando coincidencia simple
        TODO: Reemplazar con búsqueda vectorial en Qdrant
        """
        description_lower = description.lower()

        query = select(Concept).where(
            Concept.description.ilike(f"%{description_lower}%")
        ).limit(limit)

        result = await self.session.execute(query)
        concepts = result.scalars().all()

        results = [(concept, 1.0) for concept in concepts]
        return results

    async def get_similar_concepts(self, concept_code: str, limit: int = 5) -> List[Concept]:
        """
        Obtiene conceptos similares al código dado
        TODO: Implementar con embeddings y Qdrant
        """
        query = select(Concept).where(Concept.code.startswith(concept_code[:3])).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
