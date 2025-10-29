#!/bin/bash
echo "=== VERIFICACIÓN DE ESTRUCTURA ==="
MISSING=()

# Backend
[ -f "api/main.py" ] && echo "✓ api/main.py" || { echo "✗ api/main.py"; MISSING+=("api/main.py"); }
[ -f "api/routers/preview.py" ] && echo "✓ api/routers/preview.py" || { echo "✗ api/routers/preview.py"; MISSING+=("api/routers/preview.py"); }
[ -f "api/routers/recalc.py" ] && echo "✓ api/routers/recalc.py" || { echo "✗ api/routers/recalc.py"; MISSING+=("api/routers/recalc.py"); }
[ -f "api/routers/confirm.py" ] && echo "✓ api/routers/confirm.py" || { echo "✗ api/routers/confirm.py"; MISSING+=("api/routers/confirm.py"); }
[ -f "api/routers/series.py" ] && echo "✓ api/routers/series.py" || { echo "✗ api/routers/series.py"; MISSING+=("api/routers/series.py"); }
[ -f "api/services/pricing_engine.py" ] && echo "✓ api/services/pricing_engine.py" || { echo "✗ api/services/pricing_engine.py"; MISSING+=("api/services/pricing_engine.py"); }
[ -f "api/services/db.py" ] && echo "✓ api/services/db.py" || { echo "✗ api/services/db.py"; MISSING+=("api/services/db.py"); }
[ -f "api/services/cache.py" ] && echo "✓ api/services/cache.py" || { echo "✗ api/services/cache.py"; MISSING+=("api/services/cache.py"); }
[ -f "api/services/validation.py" ] && echo "✓ api/services/validation.py" || { echo "✗ api/services/validation.py"; MISSING+=("api/services/validation.py"); }

# Database
[ -f "infra/docker-compose.yml" ] && echo "✓ infra/docker-compose.yml" || { echo "✗ infra/docker-compose.yml"; MISSING+=("infra/docker-compose.yml"); }
[ -f "infra/Dockerfile.api" ] && echo "✓ infra/Dockerfile.api" || { echo "✗ infra/Dockerfile.api"; MISSING+=("infra/Dockerfile.api"); }
[ -f "db/alembic.ini" ] && echo "✓ db/alembic.ini" || { echo "✗ db/alembic.ini"; MISSING+=("db/alembic.ini"); }

# Data
[ -f "data/seed/concepts.csv" ] && echo "✓ data/seed/concepts.csv" || { echo "✗ data/seed/concepts.csv"; MISSING+=("data/seed/concepts.csv"); }
[ -f "data/etl/flow_prices.py" ] && echo "✓ data/etl/flow_prices.py" || { echo "✗ data/etl/flow_prices.py"; MISSING+=("data/etl/flow_prices.py"); }

# Web
[ -f "web/package.json" ] && echo "✓ web/package.json" || { echo "✗ web/package.json"; MISSING+=("web/package.json"); }
[ -f "web/tsconfig.json" ] && echo "✓ web/tsconfig.json" || { echo "✗ web/tsconfig.json"; MISSING+=("web/tsconfig.json"); }
[ -f "web/vite.config.ts" ] && echo "✓ web/vite.config.ts" || { echo "✗ web/vite.config.ts"; MISSING+=("web/vite.config.ts"); }

# Config
[ -f ".env.example" ] && echo "✓ .env.example" || { echo "✗ .env.example"; MISSING+=(".env.example"); }
[ -f "requirements.txt" ] && echo "✓ requirements.txt" || { echo "✗ requirements.txt"; MISSING+=("requirements.txt"); }
[ -f "README.md" ] && echo "✓ README.md" || { echo "✗ README.md"; MISSING+=("README.md"); }

echo ""
if [ ${#MISSING[@]} -eq 0 ]; then
  echo "✓ TODOS LOS ARCHIVOS ESENCIALES PRESENTES"
  exit 0
else
  echo "✗ FALTAN ${#MISSING[@]} ARCHIVOS:"
  printf '  - %s\n' "${MISSING[@]}"
  exit 1
fi
