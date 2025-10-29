# Guía de Contribución

¡Gracias por tu interés en contribuir a **Lunt**! Esta guía te ayudará a entender nuestro flujo de trabajo y estándares de código.

## Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [Cómo Contribuir](#cómo-contribuir)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Convenciones de Commits](#convenciones-de-commits)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Testing](#testing)
- [Documentación](#documentación)

## Código de Conducta

Este proyecto se adhiere a un Código de Conducta. Al participar, se espera que mantengas un ambiente respetuoso y profesional.

## Cómo Contribuir

Hay varias formas de contribuir a Lunt:

1. **Reportar Bugs**: Abre un issue con detalles del problema
2. **Solicitar Features**: Propón nuevas funcionalidades
3. **Mejorar Documentación**: Ayuda a mantener la documentación actualizada
4. **Escribir Código**: Implementa features o corrige bugs

### Reportar Bugs

Al reportar un bug, incluye:

- Descripción clara y concisa del problema
- Pasos para reproducir el bug
- Comportamiento esperado vs comportamiento actual
- Screenshots o logs (si aplica)
- Versión del software, OS, y navegador (si aplica)

### Solicitar Features

Al solicitar un feature:

- Explica el problema que resuelve
- Describe la solución propuesta
- Considera alternativas
- Evalúa el impacto en el sistema existente

## Configuración del Entorno de Desarrollo

### Requisitos

- Python 3.11+
- Node.js 20+
- Docker y Docker Compose
- Git

### Setup

1. **Fork y clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/lunt.git
   cd lunt
   ```

2. **Configurar entorno Python**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Dependencias de desarrollo
   ```

3. **Configurar pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Configurar entorno Node.js**
   ```bash
   cd web
   npm install
   ```

5. **Levantar servicios con Docker**
   ```bash
   cd infra
   docker-compose up -d
   ```

6. **Ejecutar migraciones y seed**
   ```bash
   docker-compose exec api alembic upgrade head
   docker-compose exec api python scripts/load_seed.py
   ```

## Estándares de Código

### Python (Backend)

#### Formateo
- Usar **Black** con línea de 100 caracteres
- Usar **isort** para organizar imports

```bash
black --line-length 100 api/
isort api/
```

#### Linting
- Usar **Ruff** para linting
- Seguir PEP 8

```bash
ruff check api/
```

#### Type Hints
- Usar type hints en todas las funciones
- Usar `typing` para tipos complejos

```python
from typing import Optional, List, Dict

async def get_concept(codigo: str) -> Optional[Concept]:
    """
    Obtiene un concepto por código.
    
    Args:
        codigo: Código del concepto
        
    Returns:
        Objeto Concept o None si no existe
    """
    ...
```

#### Docstrings
- Usar Google-style docstrings
- Documentar parámetros, retornos y excepciones

#### Naming Conventions
- **Variables/Funciones**: `snake_case`
- **Clases**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Privados**: `_leading_underscore`

### TypeScript (Frontend)

#### Formateo
- Usar **Prettier** con configuración del proyecto

```bash
npm run format
```

#### Linting
- Usar **ESLint** con configuración React/TypeScript

```bash
npm run lint
npm run lint:fix
```

#### Type Safety
- Strict mode activado
- Evitar `any`, usar tipos específicos
- Definir interfaces para props y state

```typescript
interface PriceBreakdownProps {
  preview: PreviewResponse
  onEdit?: (codigo: string, precio: number) => void
}

export function PriceBreakdown({ preview, onEdit }: PriceBreakdownProps) {
  // ...
}
```

#### Naming Conventions
- **Variables/Funciones**: `camelCase`
- **Componentes**: `PascalCase`
- **Interfaces**: `PascalCase` con prefijo `I` opcional
- **Types**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`

### SQL

- Usar UPPERCASE para keywords SQL
- Nombres de tablas en `snake_case`
- Nombres de columnas en `snake_case`
- Incluir índices apropiados

```sql
CREATE TABLE concept_recipes (
    id SERIAL PRIMARY KEY,
    codigo_concepto VARCHAR(20) NOT NULL,
    codigo_insumo VARCHAR(20) NOT NULL,
    cantidad NUMERIC(12, 4) NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (codigo_concepto) REFERENCES concepts(codigo),
    FOREIGN KEY (codigo_insumo) REFERENCES insumos(codigo)
);

CREATE INDEX idx_concept_recipes_concepto ON concept_recipes(codigo_concepto);
```

## Convenciones de Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/).

### Formato

```
<tipo>(<scope>): <descripción corta>

<cuerpo opcional>

<footer opcional>
```

### Tipos

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo, espacios (sin cambio de código)
- `refactor`: Refactoring de código
- `perf`: Mejora de performance
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento
- `ci`: Cambios en CI/CD
- `build`: Cambios en build system o dependencias

### Scope

- `api`: Backend FastAPI
- `web`: Frontend web
- `desktop`: Desktop app
- `db`: Base de datos / migraciones
- `etl`: ETL pipelines
- `infra`: Docker / infrastructure
- `docs`: Documentación

### Ejemplos

```bash
feat(api): agregar endpoint para exportar cotizaciones a PDF

fix(web): corregir cálculo de indirectos en tabla de precios

docs(readme): actualizar instrucciones de instalación

refactor(api): extraer lógica de pricing a servicio separado

test(api): agregar tests unitarios para pricing engine
```

### Breaking Changes

Si el commit introduce un breaking change, agregar `BREAKING CHANGE:` en el footer:

```
feat(api): cambiar estructura de respuesta de /v1/preview

BREAKING CHANGE: El campo `breakdown` ahora es un array de objetos
en lugar de un diccionario. Los clientes deben actualizar su código.
```

## Proceso de Pull Request

1. **Crear una rama feature**
   ```bash
   git checkout -b feat/nueva-funcionalidad
   # o
   git checkout -b fix/corregir-bug
   ```

2. **Hacer commits atómicos**
   - Cada commit debe ser una unidad lógica de cambio
   - Seguir convenciones de commits

3. **Mantener la rama actualizada**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Ejecutar tests**
   ```bash
   # Backend
   pytest
   
   # Frontend
   npm test
   ```

5. **Verificar code quality**
   ```bash
   # Backend
   black --check api/
   ruff check api/
   
   # Frontend
   npm run lint
   ```

6. **Push de la rama**
   ```bash
   git push origin feat/nueva-funcionalidad
   ```

7. **Crear Pull Request**
   - Título descriptivo siguiendo convenciones
   - Descripción detallada de cambios
   - Referenciar issues relacionados
   - Agregar screenshots si aplica
   - Marcar como Draft si está en progreso

### Template de PR

```markdown
## Descripción

Breve descripción de los cambios realizados.

## Tipo de cambio

- [ ] Bug fix (cambio que corrige un issue)
- [ ] Nueva funcionalidad (cambio que agrega funcionalidad)
- [ ] Breaking change (cambio que rompe compatibilidad)
- [ ] Documentación

## ¿Cómo se probó?

Describe las pruebas realizadas.

## Checklist

- [ ] Mi código sigue los estándares del proyecto
- [ ] He realizado una self-review de mi código
- [ ] He comentado áreas complejas
- [ ] He actualizado la documentación
- [ ] Mis cambios no generan nuevos warnings
- [ ] He agregado tests que prueban mi fix/feature
- [ ] Tests nuevos y existentes pasan localmente
- [ ] Cambios dependientes han sido merged

## Issues relacionados

Fixes #123
Closes #456
```

## Testing

### Backend (Pytest)

#### Estructura de Tests

```
api/tests/
├── conftest.py              # Fixtures compartidas
├── test_models.py           # Tests de modelos
├── test_pricing_engine.py   # Tests del pricing engine
├── test_routers/
│   ├── test_preview.py
│   ├── test_recalc.py
│   └── test_confirm.py
└── test_services/
    ├── test_db.py
    └── test_cache.py
```

#### Convenciones

- Un archivo de test por módulo
- Prefijo `test_` para archivos y funciones
- Usar fixtures de pytest para setup/teardown
- Tests deben ser independientes y repetibles
- Usar mocks para dependencias externas

```python
import pytest
from api.services.pricing_engine import PricingEngine

@pytest.fixture
async def pricing_engine():
    """Fixture que proporciona un pricing engine configurado."""
    return PricingEngine()

async def test_calculate_precio_unitario(pricing_engine):
    """Test que verifica el cálculo de precio unitario."""
    costo_directo = 100.0
    result = await pricing_engine.calculate_precio_unitario(costo_directo)
    
    assert result.indirectos == 15.0
    assert result.utilidad == 10.0
    assert result.precio_unitario == 125.0
```

#### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest api/tests/test_pricing_engine.py

# Con cobertura
pytest --cov=api --cov-report=html

# Verbose
pytest -v

# Detener en primer fallo
pytest -x
```

### Frontend (Vitest/Jest)

#### Estructura de Tests

```
web/src/
├── components/
│   ├── PriceBreakdownTable.tsx
│   └── PriceBreakdownTable.test.tsx
├── lib/
│   ├── api.ts
│   └── api.test.ts
└── store/
    ├── useDraft.ts
    └── useDraft.test.ts
```

#### Convenciones

- Archivo `.test.tsx` junto al componente
- Usar React Testing Library
- Tests de integración sobre tests unitarios
- Mockear API calls

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { PriceBreakdownTable } from './PriceBreakdownTable'

describe('PriceBreakdownTable', () => {
  it('renders breakdown items correctly', () => {
    const preview = {
      breakdown: [
        { codigo_insumo: 'MAT-001', descripcion: 'Block', precio_unitario: 15.50 }
      ]
    }
    
    render(<PriceBreakdownTable preview={preview} />)
    
    expect(screen.getByText('Block')).toBeInTheDocument()
    expect(screen.getByText('$15.50')).toBeInTheDocument()
  })
})
```

#### Ejecutar Tests

```bash
npm test
npm run test:coverage
```

## Documentación

### Documentación de Código

- Docstrings para funciones públicas (Python)
- JSDoc para funciones complejas (TypeScript)
- Comentarios para lógica compleja
- README en subdirectorios importantes

### Documentación de API

- Documentar endpoints en docstrings
- FastAPI genera documentación automática
- Incluir ejemplos de request/response

```python
@router.post("/preview", response_model=PreviewResponse)
async def create_preview(
    request: PreviewRequest,
    db: AsyncSession = Depends(get_db),
) -> PreviewResponse:
    """
    Genera una vista previa de cotización para un concepto.
    
    Este endpoint calcula el costo directo, indirectos, utilidad y precio
    unitario basándose en los precios actuales de insumos.
    
    Args:
        request: Datos de la solicitud (concepto, cantidad, locación)
        db: Sesión de base de datos
        
    Returns:
        Vista previa con breakdown de precios y totales
        
    Raises:
        HTTPException: Si el concepto no existe o no tiene receta
        
    Example:
        ```json
        POST /v1/preview
        {
            "codigo_concepto": "ALB-001",
            "cantidad": 100,
            "locacion_id": 1
        }
        ```
    """
    ...
```

### README y Guías

- Mantener README.md actualizado
- Agregar guías de uso para features complejas
- Documentar decisiones arquitectónicas

## Preguntas

Si tienes preguntas, puedes:

1. Abrir un issue con la etiqueta `question`
2. Consultar la documentación existente
3. Revisar issues y PRs previos

¡Gracias por contribuir a Lunt!
