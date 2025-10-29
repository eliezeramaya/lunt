# Lunt - Sistema Inteligente de Análisis, Cálculo y Gestión de Costos de Construcción

**Lunt** es una plataforma SaaS integral para el análisis, cálculo y gestión de costos de construcción. Combina pricing engine avanzado, gestión de precios históricos, recálculo dinámico y análisis de series temporales para proporcionar cotizaciones precisas e inteligentes.

## Características Principales

- **Pricing Engine**: Cálculo automático de costos directos, indirectos (15%) y utilidad (10%)
- **Gestión de Precios Históricos**: Base de datos append-only para tracking completo de precios
- **Recálculo Dinámico**: Ajuste manual de precios de insumos con recálculo automático
- **Cotizaciones Inmutables**: Sistema de versioning para quotes confirmadas
- **Análisis de Series Temporales**: Visualización de evolución de precios
- **ETL Pipeline**: Pipeline de Prefect para carga de datos desde archivos CSV/Excel
- **Caching Inteligente**: Redis para optimización de lookups de precios
- **Analytics**: Integración con Metabase para análisis y reportes
- **Search Semántico**: Qdrant para búsqueda avanzada (placeholder)
- **Storage**: MinIO S3-compatible para almacenamiento de archivos

## Stack Tecnológico

### Backend
- **FastAPI** (Python 3.11): API REST asíncrona
- **SQLAlchemy 2.0**: ORM con soporte async
- **Alembic**: Migraciones de base de datos
- **Pydantic v2**: Validación y serialización de datos
- **PostgreSQL 16**: Base de datos principal
- **Redis 7**: Cache layer
- **Prefect 3**: Orquestación de ETL pipelines

### Frontend Web
- **React 18**: UI library
- **TypeScript 5**: Type safety
- **Vite 6**: Build tool y dev server
- **TailwindCSS 3**: Utility-first CSS
- **Zustand**: State management
- **Axios**: HTTP client
- **Recharts**: Visualización de datos

### Desktop App (Planned)
- **Tauri**: Framework Rust/TypeScript
- **SQLite**: Cache local

### Infrastructure
- **Docker Compose**: Orquestación de servicios
- **Nginx**: Reverse proxy
- **Metabase**: Analytics y BI
- **Qdrant**: Vector database para search
- **MinIO**: S3-compatible object storage

## Arquitectura del Proyecto

```
lunt/
├── api/                      # Backend FastAPI
│   ├── main.py              # Entry point de la API
│   ├── models/              # SQLAlchemy models
│   │   ├── base.py
│   │   ├── concepts.py
│   │   ├── insumos.py
│   │   ├── users_locations.py
│   │   └── drafts_quotes.py
│   ├── routers/             # API endpoints
│   │   ├── preview.py       # POST /v1/preview
│   │   ├── recalc.py        # POST /v1/recalc
│   │   ├── confirm.py       # POST /v1/confirm
│   │   └── series.py        # GET/POST /v1/series/*
│   ├── services/            # Business logic
│   │   ├── db.py            # Database connections
│   │   ├── cache.py         # Redis cache
│   │   ├── pricing_engine.py  # Core pricing logic
│   │   ├── validation.py    # Input validation
│   │   └── nlu_matcher.py   # Natural language matching
│   ├── schemas/             # Pydantic schemas
│   │   ├── preview.py
│   │   ├── recalc.py
│   │   ├── confirm.py
│   │   └── series.py
│   └── tests/               # Pytest tests
│       ├── conftest.py
│       ├── test_pricing_engine.py
│       └── test_preview.py
├── db/                      # Database
│   ├── alembic/             # Migrations
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── alembic.ini
│   └── schema.sql           # Reference SQL
├── data/                    # Data management
│   ├── seed/                # Seed data
│   │   ├── concepts.csv
│   │   ├── insumos.csv
│   │   ├── concept_recipes.csv
│   │   └── insumo_precios.csv
│   └── etl/                 # ETL pipelines
│       ├── flow_prices.py   # Prefect flow
│       └── transforms.py    # Data transformations
├── web/                     # Frontend web
│   ├── src/
│   │   ├── main.tsx         # Entry point
│   │   ├── App.tsx          # Main component
│   │   ├── components/      # React components
│   │   │   ├── PriceBreakdownTable.tsx
│   │   │   └── LineSeries.tsx
│   │   ├── lib/
│   │   │   └── api.ts       # API client
│   │   └── store/
│   │       └── useDraft.ts  # Zustand store
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.cjs
├── desktop/                 # Desktop app (Tauri)
│   └── (planned)
├── infra/                   # Infrastructure
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   └── nginx/
│       └── default.conf
├── scripts/                 # Utility scripts
│   ├── load_seed.py         # Async seed data loader
│   └── smoke.sh             # Smoke tests
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## Instalación y Configuración

### Requisitos Previos

- **Docker** y **Docker Compose** (recomendado)
- **Python 3.11+** (para desarrollo local)
- **Node.js 20+** (para frontend)
- **PostgreSQL 16** (si no usas Docker)
- **Redis 7** (si no usas Docker)

### Instalación con Docker (Recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd lunt
   ```

2. **Copiar archivo de environment**
   ```bash
   cp .env.example .env
   ```

3. **Levantar servicios con Docker Compose**
   ```bash
   cd infra
   docker-compose up -d
   ```

   Esto levanta:
   - PostgreSQL (puerto 5432)
   - Redis (puerto 6379)
   - API FastAPI (puerto 8000)
   - Metabase (puerto 3001)
   - Qdrant (puerto 6333)
   - MinIO (puerto 9000, console 9001)

4. **Ejecutar migraciones**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

5. **Cargar datos de seed**
   ```bash
   docker-compose exec api python scripts/load_seed.py
   ```

6. **Verificar API**
   ```bash
   curl http://localhost:8000/health
   # Debería retornar: {"status":"ok"}
   ```

7. **Instalar dependencias del frontend**
   ```bash
   cd ../web
   npm install
   ```

8. **Ejecutar frontend en desarrollo**
   ```bash
   npm run dev
   ```

   El frontend estará disponible en `http://localhost:3000`

### Instalación Local (Sin Docker)

#### Backend

1. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones locales
   ```

4. **Ejecutar PostgreSQL y Redis**
   ```bash
   # Con Docker:
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16
   docker run -d -p 6379:6379 redis:7
   ```

5. **Ejecutar migraciones**
   ```bash
   cd db
   alembic upgrade head
   ```

6. **Cargar datos de seed**
   ```bash
   python scripts/load_seed.py
   ```

7. **Ejecutar API**
   ```bash
   cd api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend

1. **Instalar dependencias**
   ```bash
   cd web
   npm install
   ```

2. **Ejecutar en desarrollo**
   ```bash
   npm run dev
   ```

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "ok"
}
```

### Preview (Vista Previa)
```http
POST /v1/preview
Content-Type: application/json

{
  "codigo_concepto": "ALB-001",
  "cantidad": 100,
  "locacion_id": 1
}
```
**Response:**
```json
{
  "codigo_concepto": "ALB-001",
  "descripcion": "Muro de block hueco 15x20x40 cm",
  "unidad": "m2",
  "cantidad": 100,
  "breakdown": [
    {
      "codigo_insumo": "MAT-001",
      "descripcion": "Block hueco 15x20x40",
      "unidad": "pza",
      "cantidad": 12.5,
      "precio_unitario": 15.50,
      "subtotal": 193.75
    }
  ],
  "costo_directo": 2500.00,
  "indirectos": 375.00,
  "utilidad": 250.00,
  "precio_unitario": 31.25,
  "importe_total": 3125.00
}
```

### Recalculate (Recálculo con Ajustes)
```http
POST /v1/recalc
Content-Type: application/json

{
  "codigo_concepto": "ALB-001",
  "cantidad": 100,
  "adjustments": {
    "MAT-001": 16.00,
    "MAT-002": 85.00
  },
  "locacion_id": 1
}
```

### Confirm (Confirmar Cotización)
```http
POST /v1/confirm
Content-Type: application/json

{
  "codigo_concepto": "ALB-001",
  "cantidad": 100,
  "adjustments": {
    "MAT-001": 16.00
  },
  "user_id": 1,
  "locacion_id": 1
}
```
**Response:**
```json
{
  "quote_id": 42,
  "codigo_concepto": "ALB-001",
  "cantidad": 100,
  "precio_unitario": 31.50,
  "importe_total": 3150.00,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Series Histórica de Insumo
```http
POST /v1/series/insumo
Content-Type: application/json

{
  "codigo_insumo": "MAT-001",
  "locacion_id": 1
}
```

### Series Histórica de Concepto
```http
GET /v1/series/concepto?codigo_concepto=ALB-001&cantidad=100&locacion_id=1
```

## Modelos de Datos

### Concept (Concepto)
- `codigo`: Código único (ej. ALB-001)
- `descripcion`: Descripción del concepto
- `unidad`: Unidad de medida (m2, m3, pza, etc.)

### Insumo (Insumo)
- `codigo`: Código único (ej. MAT-001)
- `descripcion`: Descripción del insumo
- `unidad`: Unidad de medida
- `tipo`: material, mano_de_obra, equipo, otros

### ConceptRecipe (Receta de Concepto)
- `codigo_concepto`: FK a Concept
- `codigo_insumo`: FK a Insumo
- `cantidad`: Cantidad del insumo
- `version`: Versión de la receta

### InsumoPrice (Precio de Insumo)
- `codigo_insumo`: FK a Insumo
- `locacion_id`: FK a Location
- `precio`: Precio unitario
- `fecha_vigencia`: Fecha de vigencia
- `created_at`: Timestamp de creación (append-only)

### Quote (Cotización)
- `codigo_concepto`: FK a Concept
- `cantidad`: Cantidad cotizada
- `precio_unitario`: Precio unitario final
- `importe_total`: Importe total
- `breakdown_snapshot`: JSON con el desglose
- `adjustments_snapshot`: JSON con ajustes aplicados
- `user_id`: FK a User
- `locacion_id`: FK a Location

## Testing

### Pytest (Backend)
```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=api --cov-report=html

# Tests específicos
pytest api/tests/test_pricing_engine.py -v
```

### Smoke Tests
```bash
# Ejecutar smoke tests
chmod +x scripts/smoke.sh
./scripts/smoke.sh
```

## ETL Pipeline

### Cargar Precios desde CSV
```bash
# Ejecutar manualmente
python data/etl/flow_prices.py

# O con Prefect
prefect deployment run prices-etl/daily
```

### Formato de CSV de Precios
```csv
codigo_insumo,locacion_id,precio,fecha_vigencia
MAT-001,1,15.50,2024-01-01
MAT-002,1,80.00,2024-01-01
```

## Acceso a Servicios

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Frontend Web**: http://localhost:3000
- **Metabase**: http://localhost:3001
- **MinIO Console**: http://localhost:9001
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### Credenciales por Defecto

**PostgreSQL:**
- User: `lunt`
- Password: `lunt_password`
- Database: `lunt_db`

**MinIO:**
- Access Key: `minioadmin`
- Secret Key: `minioadmin`

**Metabase:**
- Configurar en primer acceso

## Desarrollo

### Code Style

**Python:**
- Usar **Black** para formateo
- Usar **Ruff** para linting
- Type hints obligatorios
- Docstrings en funciones públicas

```bash
# Formatear código
black api/

# Linting
ruff check api/
```

**TypeScript:**
- Usar **Prettier** para formateo
- Usar **ESLint** para linting
- Strict mode activado

```bash
# Formatear código
npm run format

# Linting
npm run lint
```

### Crear Nueva Migración
```bash
cd db
alembic revision -m "descripcion_de_la_migracion"
# Editar archivo generado en alembic/versions/
alembic upgrade head
```

### Agregar Nuevo Endpoint
1. Crear schema en `api/schemas/`
2. Crear router en `api/routers/`
3. Registrar router en `api/main.py`
4. Agregar tests en `api/tests/`

## Roadmap

### v1.0 (MVP)
- [x] Backend API con FastAPI
- [x] Modelos de datos con SQLAlchemy
- [x] Pricing engine con caching
- [x] ETL pipeline con Prefect
- [x] Frontend web con React
- [x] Docker infrastructure
- [ ] Desktop app con Tauri
- [ ] Documentación completa

### v1.1 (Mejoras)
- [ ] Autenticación y autorización (JWT)
- [ ] Multi-tenancy
- [ ] Búsqueda semántica con Qdrant
- [ ] Integración con APIs de proveedores
- [ ] Export a PDF/Excel
- [ ] Notificaciones por email

### v2.0 (AI Features)
- [ ] Predicción de precios con ML
- [ ] Recomendaciones de materiales alternativos
- [ ] Análisis de riesgo de precios
- [ ] Chat NLU para búsqueda

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de contribución.

## Licencia

[Especificar licencia]

## Soporte

Para reportar bugs o solicitar features, abrir un issue en GitHub.

## Autores

- **Equipo Lunt** - Sistema desarrollado para análisis de costos de construcción

---

**Lunt** - Análisis Inteligente de Costos de Construcción
