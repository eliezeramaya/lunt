# Metabase Dashboard Examples for Lunt Observability

Este documento contiene queries SQL de ejemplo para crear dashboards de observabilidad en Metabase.

## 📋 Setup Instructions

1. **Conectar Metabase a PostgreSQL**:

   - Abrir Metabase en http://localhost:3001
   - Admin Settings → Databases → Add Database
   - Type: PostgreSQL
   - Host: `postgres` (en Docker) o `localhost` (local)
   - Port: `5432`
   - Database: `lunt_db`
   - Username: `lunt_user`
   - Password: `lunt_pass`

2. **Crear Preguntas (Questions)** con las queries abajo

3. **Agregar a Dashboard** y configurar auto-refresh (cada 5-15 minutos)

---

## 🔢 Métricas de API - Performance

### Latencia P95 por Endpoint (Últimas 24 horas)

**Descripción**: Muestra el percentil 95 de latencia por endpoint para detectar endpoints lentos.

**Nota**: Requiere que los logs estructurados estén siendo parseados e insertados en una tabla `api_logs`.
Si no existe, crear con:

```sql
-- Tabla para logs de API (opcional, si se persisten logs)
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    level VARCHAR(20),
    http_method VARCHAR(10),
    http_path TEXT,
    status_code INTEGER,
    latency_ms NUMERIC(10,2),
    client_ip INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp DESC);
CREATE INDEX idx_api_logs_path ON api_logs(http_path);
```

**Query**:

```sql
SELECT
    http_path,
    COUNT(*) as request_count,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms), 2) as p50_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms), 2) as p95_latency_ms,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms), 2) as p99_latency_ms,
    ROUND(AVG(latency_ms), 2) as avg_latency_ms,
    ROUND(MAX(latency_ms), 2) as max_latency_ms
FROM api_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours'
    AND http_path NOT IN ('/health', '/metrics')  -- Exclude monitoring endpoints
GROUP BY http_path
ORDER BY p95_latency_ms DESC
LIMIT 20;
```

**Visualización**: Tabla o Bar Chart
**Auto-refresh**: 5 minutos

---

### Requests por Hora (Últimos 7 días)

**Query**:

```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as request_count,
    COUNT(*) FILTER (WHERE status_code >= 200 AND status_code < 300) as success_2xx,
    COUNT(*) FILTER (WHERE status_code >= 400 AND status_code < 500) as client_error_4xx,
    COUNT(*) FILTER (WHERE status_code >= 500) as server_error_5xx,
    ROUND(AVG(latency_ms), 2) as avg_latency_ms
FROM api_logs
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;
```

**Visualización**: Line Chart (múltiples series)
**X-axis**: hour
**Y-axis**: request_count, success_2xx, client_error_4xx, server_error_5xx
**Auto-refresh**: 15 minutos

---

## 🚨 Alertas - Errores 4xx y 5xx

### Series de Errores por Hora

**Descripción**: Monitorea incrementos anormales en tasas de error.

**Query**:

```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    status_code,
    COUNT(*) as error_count,
    ROUND(COUNT(*)::NUMERIC / NULLIF(
        (SELECT COUNT(*) FROM api_logs WHERE timestamp >= NOW() - INTERVAL '24 hours'), 0
    ) * 100, 2) as percentage
FROM api_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours'
    AND (status_code >= 400 OR status_code >= 500)
GROUP BY DATE_TRUNC('hour', timestamp), status_code
ORDER BY hour DESC, error_count DESC;
```

**Visualización**: Stacked Bar Chart
**Auto-refresh**: 5 minutos
**Alert**: Si error_count > 100 en una hora

---

### Top Errores 5xx con Detalles

**Query**:

```sql
SELECT
    http_path,
    http_method,
    status_code,
    COUNT(*) as occurrences,
    ROUND(AVG(latency_ms), 2) as avg_latency_ms,
    MAX(timestamp) as last_seen
FROM api_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours'
    AND status_code >= 500
GROUP BY http_path, http_method, status_code
ORDER BY occurrences DESC
LIMIT 20;
```

**Visualización**: Tabla
**Auto-refresh**: 5 minutos

---

## 💰 Business Metrics - Precios y Conceptos

### Actividad de Cotizaciones por Día

**Query**:

```sql
SELECT
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) FILTER (WHERE status = 'draft') as drafts_created,
    COUNT(*) FILTER (WHERE status = 'confirmed') as quotes_confirmed,
    SUM(total_amount) FILTER (WHERE status = 'confirmed') as total_quoted_value
FROM quotes
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Visualización**: Line Chart
**Auto-refresh**: 1 hora

---

### Conceptos Más Cotizados (Top 20)

**Query**:

```sql
SELECT
    c.code,
    c.name,
    COUNT(DISTINCT q.id) as quote_count,
    COUNT(DISTINCT q.user_id) as unique_users,
    ROUND(AVG(cr.quantity), 2) as avg_quantity_used
FROM concepts c
INNER JOIN concept_recipes cr ON c.id = cr.concept_id
INNER JOIN quotes q ON q.id = cr.quote_id  -- Adjust join based on schema
WHERE q.created_at >= NOW() - INTERVAL '90 days'
GROUP BY c.code, c.name
ORDER BY quote_count DESC
LIMIT 20;
```

**Visualización**: Bar Chart
**Auto-refresh**: 1 hora

---

### Volatilidad de Precios por Insumo (Últimos 6 meses)

**Descripción**: Detecta insumos con alta volatilidad de precios.

**Query**:

```sql
SELECT
    i.code,
    i.name,
    i.unit,
    l.code as location,
    COUNT(*) as price_updates,
    ROUND(AVG(ip.price), 2) as avg_price,
    ROUND(STDDEV(ip.price), 2) as price_stddev,
    ROUND(STDDEV(ip.price) / NULLIF(AVG(ip.price), 0) * 100, 2) as coefficient_of_variation
FROM insumos i
INNER JOIN insumo_prices ip ON i.id = ip.insumo_id
INNER JOIN locations l ON ip.location_id = l.id
WHERE ip.valid_from >= NOW() - INTERVAL '6 months'
GROUP BY i.code, i.name, i.unit, l.code
HAVING COUNT(*) >= 3  -- At least 3 price points
ORDER BY coefficient_of_variation DESC
LIMIT 30;
```

**Visualización**: Tabla con highlighting en coefficient_of_variation > 20%
**Auto-refresh**: 1 día

---

## 📊 Time Series - Vista Materializada

### Serie de Precios Mensuales por Concepto

**Descripción**: Usa la vista materializada `concept_pu_mensual` para gráficas rápidas.

**Query**:

```sql
SELECT
    month,
    concept_code,
    concept_name,
    location_code,
    base_price_avg,
    price_with_indirect,
    final_unit_price,
    price_samples
FROM concept_pu_mensual
WHERE concept_code IN ('CON-001', 'CON-002', 'CON-003')  -- Filtrar conceptos específicos
    AND month >= NOW() - INTERVAL '12 months'
ORDER BY concept_code, month DESC;
```

**Parámetros**: Añadir parámetro `concept_code` para filtro dinámico
**Visualización**: Line Chart (múltiples series por concepto)
**X-axis**: month
**Y-axis**: final_unit_price
**Auto-refresh**: 1 hora

---

### Comparación Regional de Precios

**Query**:

```sql
SELECT
    month,
    concept_code,
    location_code,
    final_unit_price,
    price_samples,
    RANK() OVER (PARTITION BY concept_code, month ORDER BY final_unit_price DESC) as price_rank
FROM concept_pu_mensual
WHERE month >= NOW() - INTERVAL '6 months'
    AND concept_code = 'CON-001'  -- Parametrizar
ORDER BY month DESC, price_rank;
```

**Visualización**: Grouped Bar Chart
**Auto-refresh**: 1 hora

---

## 🔍 Health Check Dashboard

### Resumen Ejecutivo (Single Stat Cards)

**Total Requests (24h)**:

```sql
SELECT COUNT(*) FROM api_logs WHERE timestamp >= NOW() - INTERVAL '24 hours';
```

**Success Rate (24h)**:

```sql
SELECT
    ROUND(
        COUNT(*) FILTER (WHERE status_code >= 200 AND status_code < 300)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as success_rate_percent
FROM api_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours';
```

**Avg Response Time (24h)**:

```sql
SELECT ROUND(AVG(latency_ms), 2) as avg_latency_ms
FROM api_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours';
```

**Active Users (24h)**:

```sql
SELECT COUNT(DISTINCT user_id) FROM quotes WHERE created_at >= NOW() - INTERVAL '24 hours';
```

---

## 📌 Notas Importantes

1. **Tabla api_logs**: Si persistes logs estructurados, crear tabla como se muestra arriba.
   Alternativamente, usar herramientas como Loki/Grafana para logs sin DB.

2. **Refresh de MV**: El ETL refresca `concept_precios_mensuales` automáticamente.
   Para refresh manual:

   ```sql
   REFRESH MATERIALIZED VIEW CONCURRENTLY concept_precios_mensuales;
   ```

3. **Performance**: Las queries usan índices creados en migration 002.
   Verificar con `EXPLAIN ANALYZE` si son lentas.

4. **Alertas**: Configurar notificaciones en Metabase:

   - Admin → Pulses → New Pulse
   - Condiciones: error_count > threshold

5. **Ejemplo de log JSON parseado**:
   Si procesas logs con Logstash/Fluentd, pueden insertarse en `api_logs`:
   ```json
   {
     "timestamp": "2025-10-28T12:34:56Z",
     "level": "INFO",
     "http_method": "POST",
     "http_path": "/v1/preview",
     "status_code": 200,
     "latency_ms": 45.23,
     "client_ip": "192.168.1.100"
   }
   ```

---

## 🚀 Quick Start

1. Ejecutar migración para crear MV:

   ```bash
   alembic upgrade head
   ```

2. Conectar Metabase a PostgreSQL (instrucciones arriba)

3. Crear preguntas usando las queries de este documento

4. Agrupar en dashboard "Lunt Observability"

5. Configurar auto-refresh y alertas

---

**Última actualización**: 2025-10-28
**Autor**: Equipo Lunt
