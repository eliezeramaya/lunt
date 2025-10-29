-- Lunt Database Schema
-- PostgreSQL 16+
-- This file serves as reference documentation
-- Actual schema is managed by Alembic migrations

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Locations Table
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    state VARCHAR(50),
    country VARCHAR(50) NOT NULL DEFAULT 'Mexico',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_locations_code ON locations(code);

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Concepts Table
CREATE TABLE concepts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    category VARCHAR(100),
    embedding_vector TEXT,  -- Placeholder for Qdrant vector ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_concepts_code ON concepts(code);
CREATE INDEX idx_concepts_description_gin ON concepts USING gin(description gin_trgm_ops);

-- Insumos Table
CREATE TABLE insumos (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_insumos_code ON insumos(code);
CREATE INDEX idx_insumos_category ON insumos(category);

-- Concept Recipes Table
CREATE TABLE concept_recipes (
    id SERIAL PRIMARY KEY,
    concept_id INTEGER REFERENCES concepts(id) NOT NULL,
    insumo_id INTEGER REFERENCES insumos(id) NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_concept_recipes_concept ON concept_recipes(concept_id, valid_from, valid_until);
CREATE INDEX idx_concept_recipes_insumo ON concept_recipes(insumo_id);

-- Insumo Prices Table (Append-Only)
CREATE TABLE insumo_prices (
    id SERIAL PRIMARY KEY,
    insumo_id INTEGER REFERENCES insumos(id) NOT NULL,
    location_code VARCHAR(20) NOT NULL,
    price NUMERIC(12, 4) NOT NULL,
    currency VARCHAR(3) DEFAULT 'MXN' NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE,
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_insumo_prices_location_date ON insumo_prices(insumo_id, location_code, valid_from DESC);

-- Drafts Table
CREATE TABLE drafts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    concept_code VARCHAR(50) NOT NULL,
    concept_description TEXT NOT NULL,
    location_code VARCHAR(20) NOT NULL,
    calculation_date TIMESTAMP NOT NULL,
    breakdown JSONB NOT NULL,
    costo_directo NUMERIC(12, 4) NOT NULL,
    indirectos NUMERIC(12, 4) NOT NULL,
    utilidad NUMERIC(12, 4) NOT NULL,
    precio_unitario NUMERIC(12, 4) NOT NULL,
    indirect_percentage NUMERIC(5, 4) NOT NULL,
    utility_percentage NUMERIC(5, 4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_drafts_user_date ON drafts(user_id, calculation_date);

-- Quotes Table (Immutable)
CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    draft_id INTEGER REFERENCES drafts(id),
    quote_number VARCHAR(50) UNIQUE NOT NULL,
    concept_code VARCHAR(50) NOT NULL,
    concept_description TEXT NOT NULL,
    location_code VARCHAR(20) NOT NULL,
    calculation_date TIMESTAMP NOT NULL,
    breakdown JSONB NOT NULL,
    costo_directo NUMERIC(12, 4) NOT NULL,
    indirectos NUMERIC(12, 4) NOT NULL,
    utilidad NUMERIC(12, 4) NOT NULL,
    precio_unitario NUMERIC(12, 4) NOT NULL,
    indirect_percentage NUMERIC(5, 4) NOT NULL,
    utility_percentage NUMERIC(5, 4) NOT NULL,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'confirmed' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_quotes_number ON quotes(quote_number);
CREATE INDEX idx_quotes_user_date ON quotes(user_id, calculation_date);
CREATE INDEX idx_quotes_concept ON quotes(concept_code);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_locations_updated_at BEFORE UPDATE ON locations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON concepts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_insumos_updated_at BEFORE UPDATE ON insumos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_concept_recipes_updated_at BEFORE UPDATE ON concept_recipes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_insumo_prices_updated_at BEFORE UPDATE ON insumo_prices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_drafts_updated_at BEFORE UPDATE ON drafts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON quotes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
