# 📊 Sistema de Auditoría Continua para Lunt

Este directorio contiene el sistema completo de auditoría automatizada que verifica la salud y calidad del proyecto Lunt mediante **scripts locales idempotentes** y **integración con GitHub Actions**.

---

## 🎯 Propósito

El sistema de auditoría proporciona:

- ✅ **Verificación automática semanal** del estado del proyecto
- 🔍 **Ejecución bajo demanda** (local o CI/CD)
- 📝 **Reportes consolidados** con métricas Pass/Fail/Skip
- 🛡️ **Tolerancia a fallos**: continúa aunque fallen checks individuales
- 📦 **Artefactos históricos**: logs y summaries en `audits/history/`

---

## 📁 Estructura de Directorios

```
audits/
├── README.md                   # 📘 Este archivo
├── run_local_audit.sh          # 🔧 Script maestro de auditoría local
├── tools/
│   └── now.sh                  # ⏰ Generador de timestamp (YYYYMMDD-HHMMSS)
├── ci/
│   └── report_merge.py         # 📊 Consolidador de reportes para CI/CD
└── history/                    # 📦 Historial de auditorías
    ├── 20241115-143000/
    │   ├── SUMMARY.md          # Resumen con tabla de resultados
    │   ├── tree.txt            # Estructura del repositorio
    │   └── logs/               # Logs detallados de cada check
    │       ├── 01-STRUCTURE.log
    │       ├── 02-LINT-PYTHON.log
    │       ├── ...
    │       └── 10-WEB-BUILD.log
    └── 20241122-090000/
        └── ...
```

---

## 🚀 Ejecución Local

### Requisitos Previos

| Herramienta                 | Requerido      | Propósito                    |
| --------------------------- | -------------- | ---------------------------- |
| `bash`                      | ✅ Sí          | Ejecución del script maestro |
| `python` 3.12+              | ⚠️ Recomendado | Checks de linting y tests    |
| `venv` activo               | ⚠️ Recomendado | Dependencias Python          |
| `docker` + `docker compose` | ⚠️ Opcional    | Verificación de servicios    |
| `tree`, `curl`, `nc`        | ⚠️ Opcional    | Checks auxiliares            |
| `node` + `npm`              | ⚠️ Opcional    | Verificación del frontend    |

**Nota**: El sistema es **tolerante**: si falta una herramienta, marca el check como **SKIP** en lugar de fallar.

---

### Ejecución Básica

```bash
# Desde la raíz del proyecto Lunt
bash audits/run_local_audit.sh
```

### Output Esperado

El script genera:

1. **Directorio timestamped**: `audits/history/YYYYMMDD-HHMMSS/`
2. **SUMMARY.md**: Tabla con resultados Pass/Fail/Skip
3. **tree.txt**: Estructura del repositorio
4. **logs/\*.log**: Logs detallados de cada verificación

### Interpretación de Resultados

| Estado      | Significado               | Acción Requerida                     |
| ----------- | ------------------------- | ------------------------------------ |
| ✅ **PASS** | Check exitoso             | Ninguna                              |
| ❌ **FAIL** | Check falló               | Revisar log específico en `logs/`    |
| ⏭️ **SKIP** | Dependencia no disponible | Instalar herramienta si es necesaria |

---

## 🔍 Checks Implementados

El script ejecuta **10 verificaciones independientes**:

### 1. **STRUCTURE** - Estructura del Repositorio

- **Qué verifica**: Existencia de archivos esenciales
- **Herramientas**: `tree`, verificación de archivos
- **Archivos clave**:
  - `pyproject.toml`, `requirements.txt`
  - `api/main.py`, `api/routers/`, `api/models/`
  - `alembic.ini`, `migrations/versions/`
  - `web/package.json`, `web/src/`, `web/public/`
- **Falla si**: Faltan archivos críticos

### 2. **LINT-PYTHON** - Linting de Python

- **Qué verifica**: Calidad del código Python con `ruff` y `black`
- **Herramientas**: `ruff check .`, `black --check .`
- **Requisitos**: Virtual environment activado
- **Falla si**: Hay errores de linting o formato
- **Skip si**: No hay venv o no están instalados ruff/black

### 3. **LINT-WEB** - Linting del Frontend

- **Qué verifica**: Calidad del código TypeScript/React
- **Herramientas**: `eslint`, `prettier`
- **Directorio**: `web/`
- **Falla si**: Hay errores de linting o formato
- **Skip si**: No existe `web/package.json` o no están instaladas las herramientas

### 4. **DOCKER** - Estado de Docker Compose

- **Qué verifica**: Validez de `docker-compose.yml` y estado de contenedores
- **Comandos**: `docker compose config`, `docker compose ps`
- **Falla si**: Configuración inválida o servicios no corriendo
- **Skip si**: Docker no está instalado o no hay `docker-compose.yml`

### 5. **ALEMBIC** - Migraciones de Base de Datos

- **Qué verifica**: Estado de migraciones con Alembic
- **Comandos**: `alembic current`, `alembic history`
- **Falla si**: No hay migraciones aplicadas o historial vacío
- **Skip si**: No existe `alembic.ini`

### 6. **SEED** - Scripts de Seed Data

- **Qué verifica**: Existencia de scripts de carga de datos
- **Archivos**: `scripts/load_seed.py` o similar
- **Falla si**: No existen scripts de seed
- **Skip si**: N/A (verifica existencia)

### 7. **API** - Salud de la API

- **Qué verifica**: Endpoints activos de FastAPI
- **Endpoints**:
  - `GET http://localhost:8000/health`
  - `POST http://localhost:8000/v1/preview`
- **Falla si**: API no responde o retorna errores
- **Skip si**: Puerto 8000 no está escuchando

### 8. **PYTEST** - Suite de Tests

- **Qué verifica**: Ejecución de tests con pytest
- **Comando**: `PYTHONPATH=. pytest -v`
- **Falla si**: Algún test falla
- **Skip si**: pytest no está instalado o no hay tests

### 9. **ETL** - Scripts ETL

- **Qué verifica**: Existencia de scripts ETL/data processing
- **Directorios**: `etl/`, `data/etl/`, `scripts/etl/`
- **Falla si**: No existen scripts ETL
- **Skip si**: N/A (verifica existencia)

### 10. **WEB-BUILD** - Build del Frontend

- **Qué verifica**: Compilación exitosa del frontend
- **Comando**: `npm run build` en `web/`
- **Directorio output**: `web/dist/`
- **Falla si**: Build falla o no genera `dist/`
- **Skip si**: No existe `web/package.json` o no hay node_modules

---

## 📄 Formato del SUMMARY.md

Cada auditoría genera un `SUMMARY.md` con el siguiente formato:

```markdown
# Lunt Audit Report

**Timestamp**: 2024-11-22 09:00:15 CST
**Branch**: `main`
**Commit**: `a1b2c3d`
**Host**: `lunt-ci-runner`
**User**: `github-actions`

## Statistics

| Metric  | Value |
| ------- | ----- |
| Passed  | 8     |
| Failed  | 1     |
| Skipped | 1     |

## Check Results

| #   | Check Name  | Status  | Log File                  |
| --- | ----------- | ------- | ------------------------- |
| 01  | STRUCTURE   | ✅ PASS | `logs/01-STRUCTURE.log`   |
| 02  | LINT-PYTHON | ✅ PASS | `logs/02-LINT-PYTHON.log` |
| 03  | LINT-WEB    | ⏭️ SKIP | `logs/03-LINT-WEB.log`    |
| 04  | DOCKER      | ✅ PASS | `logs/04-DOCKER.log`      |
| 05  | ALEMBIC     | ✅ PASS | `logs/05-ALEMBIC.log`     |
| 06  | SEED        | ✅ PASS | `logs/06-SEED.log`        |
| 07  | API         | ❌ FAIL | `logs/07-API.log`         |
| 08  | PYTEST      | ✅ PASS | `logs/08-PYTEST.log`      |
| 09  | ETL         | ✅ PASS | `logs/09-ETL.log`         |
| 10  | WEB-BUILD   | ✅ PASS | `logs/10-WEB-BUILD.log`   |

---

**Final Status**: AUDIT FAILED ❌
_Review failed checks in the logs/ directory_
```

---

## ☁️ Integración con GitHub Actions

### Workflow: `.github/workflows/continuous-audit.yml`

El sistema se ejecuta automáticamente en:

1. **Semanal**: Domingos a las 3:00 AM (hora de México)
2. **Manual**: Botón "Run workflow" en GitHub Actions UI
3. **Pull Requests**: Automáticamente en PRs a `main` o `dev/**`

### Artefactos Generados

Cada ejecución en CI publica:

- **audit-report-YYYYMMDD-HHMMSS**: Directorio completo con SUMMARY + logs
- **audit-logs-YYYYMMDD-HHMMSS**: Solo los logs (para revisión rápida)

**Retención**: 30 días

### Job Summary

GitHub Actions publica un resumen visual en la pestaña "Summary" con:

- 📊 Tabla de estadísticas (Pass/Fail/Skip)
- 🔍 Lista de logs con tamaños
- 🔗 Links a artefactos descargables
- 🟢/🔴/🟡 Badge de estado

---

## 🛠️ Troubleshooting

### Problema: "Docker not found - SKIP"

**Causa**: Docker no está instalado o no está en PATH
**Solución**: Instalar Docker Engine o Docker Desktop

### Problema: "Python venv not activated - SKIP"

**Causa**: No hay virtual environment activado
**Solución**:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### Problema: "API health check failed"

**Causa**: FastAPI no está corriendo en localhost:8000
**Solución**:

```bash
docker compose up -d  # Levantar servicios
# O ejecutar manualmente:
cd api && uvicorn main:app --reload
```

### Problema: "Multiple checks marked as SKIP"

**Causa**: Entorno incompleto (falta Docker, venv, o herramientas)
**Solución**: Revisar logs específicos en `logs/*.log` para ver qué falta

---

## 🔧 Personalización

### Agregar un Nuevo Check

1. Editar `audits/run_local_audit.sh`
2. Copiar template de función existente (ej. `check_01_structure`)
3. Implementar lógica de verificación:

   ```bash
   check_11_custom_verification() {
     local CHECK="11-CUSTOM"
     local OUT="${LOG_DIR}/${CHECK}.log"
     log_info "Running Custom Verification..."

     # Tu lógica aquí
     if [ ... ]; then
       record_result "$CHECK" "PASS"
     else
       record_result "$CHECK" "FAIL"
     fi
   }
   ```

4. Llamar desde `main()`: `check_11_custom_verification`

### Modificar Frecuencia en CI

Editar `.github/workflows/continuous-audit.yml`:

```yaml
schedule:
  - cron: "0 15 * * 1,3,5" # Lunes, Miércoles, Viernes a las 3 PM
```

---

## 📚 Referencias

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Bash Exit Codes](https://tldp.org/LDP/abs/html/exitcodes.html)
- [Docker Compose CLI](https://docs.docker.com/compose/reference/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [pytest Docs](https://docs.pytest.org/)

---

## 📞 Soporte

Para reportar problemas con el sistema de auditoría:

1. Revisar logs en `audits/history/<timestamp>/logs/`
2. Buscar issues existentes en el repositorio
3. Crear nuevo issue con:
   - Timestamp de la auditoría fallida
   - Logs relevantes (adjuntar archivos)
   - Entorno (local vs CI/CD)

---

**Última actualización**: 2024-11-22
**Versión del sistema**: 1.0.0
**Autor**: Equipo Lunt
