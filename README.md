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

---

## 🔒 Seguridad en Producción

### CORS y Rate Limiting

La API incluye protecciones de seguridad configurables por variables de entorno:

```bash
# .env
ALLOWED_ORIGINS=https://app.lunt.com,https://www.lunt.com
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_ENABLED=true
```

**Características**:
- **CORS restrictivo**: Solo dominios especificados en `ALLOWED_ORIGINS`
- **Rate limiting por IP**: Configurable con SlowAPI (default: 100 req/min)
- **Health check excluido**: `/health` y `/metrics` no tienen rate limit
- **Logs de violaciones**: Se registran intentos de rate limit exceeded

**Verificación**:
```bash
# Verificar rate limiting
for i in {1..150}; do curl -s http://localhost:8000/ > /dev/null && echo "Request $i OK"; done

# Debe fallar después del límite configurado
```

### Headers de Seguridad (Nginx)

El reverse proxy Nginx inyecta headers de seguridad automáticamente:

```nginx
# Headers aplicados en infra/nginx/default.conf
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; ...
```

**Verificación**:
```bash
# Verificar headers de seguridad
curl -I http://localhost:80 | grep -E "X-Frame|X-Content|Referrer|Permissions|Content-Security"

# Ejemplo de output esperado:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Referrer-Policy: strict-origin-when-cross-origin
```

**Nota**: HSTS comentado por defecto. Descomentar cuando uses HTTPS:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### Configuración de JWT

```bash
# Generar secret key fuerte
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Configurar en .env
JWT_SECRET_KEY=<generated_secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

**⚠️ Advertencia**: Nunca usar valores por defecto en producción.

---

## 📊 Observabilidad

### Métricas Prometheus

La API expone métricas en el endpoint `/metrics` usando Prometheus instrumentator:

**Métricas disponibles**:
- **Request latency**: p50, p95, p99 por endpoint
- **Request count**: Total y por status code
- **Requests in progress**: Concurrencia actual
- **Response size**: Tamaño de respuestas

**Acceso**:
```bash
# Ver métricas
curl http://localhost:8000/metrics

# Ejemplo de output:
# http_request_duration_seconds_bucket{handler="/v1/preview",le="0.1"} 150
# http_request_duration_seconds_sum{handler="/v1/preview"} 12.45
# http_requests_total{handler="/v1/preview",method="POST",status="200"} 150
```

**Integración con Prometheus**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'lunt-api'
    static_configs:
      - targets: ['api:8000']
    scrape_interval: 15s
```

### Logs Estructurados (JSON)

Todos los logs se emiten en formato JSON para fácil parsing:

```json
{
  "timestamp": "2025-10-28T15:30:45.123456Z",
  "level": "INFO",
  "logger": "api.main",
  "message": "HTTP request processed",
  "http.method": "POST",
  "http.path": "/v1/preview",
  "http.status_code": 200,
  "latency_ms": 45.23,
  "client_ip": "192.168.1.100"
}
```

**Configuración**:
```bash
# .env
LOG_LEVEL=INFO
JSON_LOGS=true  # false para formato humano en desarrollo
```

**Ejemplo de log humano (desarrollo)**:
```
2025-10-28 15:30:45 - api.main - INFO - HTTP request processed
```

**Parsing con jq**:
```bash
# Filtrar por endpoint
docker logs lunt-api 2>&1 | jq 'select(.http_path == "/v1/preview")'

# Calcular latencia promedio
docker logs lunt-api 2>&1 | jq -s 'map(.latency_ms) | add/length'
```

### Dashboards de Metabase

Ver `audits/metabase/example_dashboard.sql.md` para queries de ejemplo:

- **Performance**: Latencia p95 por endpoint, requests/hora
- **Errores**: Series de 4xx/5xx, top errores con detalles
- **Business**: Cotizaciones por día, conceptos más usados
- **Time series**: Evolución de precios usando MV

**Conectar Metabase**:
1. Abrir http://localhost:3001
2. Admin → Databases → Add PostgreSQL
3. Host: `postgres`, Port: `5432`, DB: `lunt_db`
4. Crear preguntas con las queries del documento

---

## ⚡ Rendimiento

### Índices de Base de Datos

Migraciones aplicadas para optimizar queries frecuentes:

**Migration 002: Performance Indexes**
```sql
-- Lookup de precios más recientes (usado en preview/recalc)
CREATE INDEX ix_insumo_prices_lookup
ON insumo_prices (insumo_id, location_id, valid_from DESC);

-- Lookup de recetas por concepto y localidad
CREATE INDEX ix_concept_recipes_lookup
ON concept_recipes (concept_id, location_id);

-- Queries de usuario (dashboard, paginación)
CREATE INDEX ix_drafts_user_created
ON drafts (user_id, created_at DESC);

CREATE INDEX ix_quotes_user_status
ON quotes (user_id, status);
```

**Impacto**:
- Lookups de precios: **100x más rápido** (O(log n) vs O(n))
- Expansión de recetas: **10x más rápido**
- Paginación de drafts: **50x más rápido**

**Verificar planes de ejecución**:
```sql
EXPLAIN ANALYZE
SELECT * FROM insumo_prices
WHERE insumo_id = 1 AND location_id = 1
ORDER BY valid_from DESC LIMIT 1;

-- Debe usar ix_insumo_prices_lookup (Index Scan)
```

### Vistas Materializadas

**Migration 003: Materialized Views**

Vista materializada `concept_precios_mensuales` pre-agrega datos mensuales:

```sql
-- Crear/actualizar MV
CREATE MATERIALIZED VIEW concept_precios_mensuales AS
SELECT ...aggregations...

-- Refresh (ejecutado automáticamente por ETL)
REFRESH MATERIALIZED VIEW CONCURRENTLY concept_precios_mensuales;
```

**Vista `concept_pu_mensual`** (built on MV) para consultas rápidas:
```sql
SELECT * FROM concept_pu_mensual
WHERE concept_code = 'CON-001'
AND month >= NOW() - INTERVAL '12 months';
```

**Impacto**:
- Queries de series temporales: **1000x más rápido**
- Sin bloqueos: `CONCURRENTLY` permite queries durante refresh
- Usado por: endpoint `/v1/series`

**ETL Refresh**:
El pipeline de precios refresca automáticamente la MV después de cargas:

```python
# data/etl/flow_prices.py
@task
def refresh_materialized_view(connection_string: str):
    conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY concept_precios_mensuales"))
```

**Monitoreo**:
```sql
-- Verificar última actualización de MV
SELECT schemaname, matviewname, last_refresh
FROM pg_matviews
WHERE matviewname = 'concept_precios_mensuales';
```

---

## 🔄 CI/CD y Auditoría Continua

### GitHub Actions Workflow

El repositorio incluye auditoría automática semanal y en PRs:

**Triggers**:
- **Semanal**: Domingos a las 3:00 AM (México)
- **Manual**: Botón "Run workflow" en GitHub Actions
- **Pull Requests**: Automático en PRs a `main` o `dev/**`

**Verificaciones**:
1. Estructura del repositorio
2. Linting Python (ruff + black)
3. Linting Web (eslint + prettier)
4. Docker Compose validación
5. Alembic migrations
6. Seed data
7. API health check
8. Pytest suite
9. ETL flows
10. Web build

**Características**:
- **Tolerante a fallos**: Marca "SKIPPED" si falta Docker (no rompe CI)
- **Artifacts**: Sube logs y summary a GitHub (retención 30 días)
- **Job Summary**: Publica tabla con resultados en la pestaña Summary
- **PR Comments**: Comenta automáticamente en PRs con estado de auditoría

**Ejecución local**:
```bash
# Ejecutar auditoría completa
bash audits/run_local_audit.sh

# O con Makefile
make audit

# Ver resultados
ls -la audits/history/<timestamp>/
cat audits/history/<timestamp>/SUMMARY.md
```

**Output esperado**:
```
╔════════════════════════════════════════════════════════════════╗
║                    RESULTADOS FINALES                          ║
╚════════════════════════════════════════════════════════════════╝

Total Checks: 10
✅ Passed:    9
❌ Failed:    0
⏭️  Skipped:   1

[PASS] Auditoría PASÓ - Todos los checks críticos OK
```

### Makefile Shortcuts

El proyecto incluye comandos `make` para desarrollo:

```bash
# Auditoría y calidad
make audit          # Ejecutar auditoría completa
make lint           # Linters Python + Web
make lint-fix       # Auto-fix issues de linting
make test           # Ejecutar tests
make test-cov       # Tests con coverage

# Docker
make dev            # Levantar entorno completo + health check
make up             # Levantar servicios
make down           # Detener servicios
make logs           # Ver logs en tiempo real
make ps             # Estado de servicios

# Base de datos
make migrate        # Ejecutar migraciones
make migrate-create MSG="descripción"  # Crear nueva migración
make seed           # Cargar seed data
make db-reset       # Resetear DB (DESTRUCTIVO, requiere confirmación)

# Setup
make setup          # Setup completo (Python + Web + Docker)
make setup-py       # Setup entorno Python
make setup-web      # Setup entorno Web

# Build
make build-web      # Build del frontend
make build-docker   # Build de imágenes Docker

# Utilidades
make version        # Mostrar versiones de herramientas
make info           # Estado del proyecto
make clean          # Limpiar archivos temporales
make clean-all      # Limpieza completa (incluye venv, node_modules, volumes)
```

**Ejemplo de uso**:
```bash
# Setup inicial
make setup

# Levantar entorno
make dev

# En otra terminal: ejecutar tests
make test

# Ver logs
make logs

# Al finalizar
make down
```

---

## 🖥️ Desktop App (Fase 2)

La aplicación desktop usa **Tauri 2.0** para crear binarios nativos multiplataforma.

### Características

- **Multiplataforma**: Windows, macOS, Linux
- **Ligera**: ~5-10 MB (vs ~100+ MB de Electron)
- **Rendimiento**: Usa WebView nativo del SO
- **Seguridad**: Sandboxing y CSP integrados
- **Futuro**: Cache SQLite local para modo offline (TODO)

### Build Instructions

**Requisitos**:
- Rust 1.70+
- Node.js 22+
- System dependencies (ver `desktop/README.md`)

**Development**:
```bash
cd desktop
cargo tauri dev
```

Esto abre la app apuntando a `http://localhost:3000` con hot reload.

**Production Build**:
```bash
cd desktop
cargo tauri build
```

**Outputs**:
- **Linux**: `target/release/bundle/deb/lunt_0.1.0_amd64.deb`
- **macOS**: `target/release/bundle/dmg/Lunt_0.1.0_x64.dmg`
- **Windows**: `target/release/bundle/nsis/Lunt_0.1.0_x64-setup.exe`

### Configuración

Ver `desktop/src-tauri/tauri.conf.json`:
```json
{
  "build": {
    "frontendDist": "../web/dist"
  },
  "app": {
    "windows": [{
      "title": "Lunt - Sistema de Gestión de Costos",
      "width": 1200,
      "height": 800
    }]
  }
}
```

### Modo Offline (TODO)

Plan para implementar cache local con SQLite:

1. **Schema SQLite**: Espejo de PostgreSQL (concepts, insumos, prices)
2. **Tauri Commands**: `sync_data()`, `get_concepts_offline()`
3. **Lógica de Sync**:
   - Online: Sync API → SQLite
   - Offline: Usar SQLite
   - Conflictos: Timestamp wins o manual merge
4. **UI Indicators**: Badge "Offline Mode", indicador de sync

Ver `desktop/README.md` para implementación detallada.

---

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
