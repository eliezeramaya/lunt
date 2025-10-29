"""
Create initial database schema

Creates all tables for Lunt system including:
- locations: Geographic locations for regional pricing
- users: User accounts
- concepts: Construction concepts/activities
- insumos: Materials, labor, equipment inputs
- concept_recipes: Recipes linking concepts to insumos
- insumo_prices: Historical price data for insumos
- drafts: Draft calculations in progress
- quotes: Confirmed immutable quotes

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_locations_code'), 'locations', ['code'], unique=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'concepts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('embedding_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_concepts_code'), 'concepts', ['code'], unique=True)

    op.create_table(
        'insumos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_insumos_code'), 'insumos', ['code'], unique=True)
    op.create_index(op.f('ix_insumos_category'), 'insumos', ['category'], unique=False)

    op.create_table(
        'concept_recipes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=False),
        sa.Column('insumo_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ),
        sa.ForeignKeyConstraint(['insumo_id'], ['insumos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_concept_recipes_concept_valid'), 'concept_recipes', ['concept_id', 'valid_from', 'valid_until'], unique=False)
    op.create_index(op.f('ix_concept_recipes_insumo'), 'concept_recipes', ['insumo_id'], unique=False)

    op.create_table(
        'insumo_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('insumo_id', sa.Integer(), nullable=False),
        sa.Column('location_code', sa.String(length=20), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['insumo_id'], ['insumos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_insumo_prices_insumo'), 'insumo_prices', ['insumo_id'], unique=False)
    op.create_index(op.f('ix_insumo_prices_location_date'), 'insumo_prices', ['insumo_id', 'location_code', 'valid_from'], unique=False)

    op.create_table(
        'drafts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('concept_code', sa.String(length=50), nullable=False),
        sa.Column('concept_description', sa.Text(), nullable=False),
        sa.Column('location_code', sa.String(length=20), nullable=False),
        sa.Column('calculation_date', sa.DateTime(), nullable=False),
        sa.Column('breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('costo_directo', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('indirectos', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('utilidad', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('indirect_percentage', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('utility_percentage', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drafts_user_date'), 'drafts', ['user_id', 'calculation_date'], unique=False)

    op.create_table(
        'quotes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('draft_id', sa.Integer(), nullable=True),
        sa.Column('quote_number', sa.String(length=50), nullable=False),
        sa.Column('concept_code', sa.String(length=50), nullable=False),
        sa.Column('concept_description', sa.Text(), nullable=False),
        sa.Column('location_code', sa.String(length=20), nullable=False),
        sa.Column('calculation_date', sa.DateTime(), nullable=False),
        sa.Column('breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('costo_directo', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('indirectos', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('utilidad', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('indirect_percentage', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('utility_percentage', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quote_number')
    )
    op.create_index(op.f('ix_quotes_quote_number'), 'quotes', ['quote_number'], unique=True)
    op.create_index(op.f('ix_quotes_user_date'), 'quotes', ['user_id', 'calculation_date'], unique=False)
    op.create_index(op.f('ix_quotes_concept'), 'quotes', ['concept_code'], unique=False)


def downgrade() -> None:
    op.drop_table('quotes')
    op.drop_table('drafts')
    op.drop_table('insumo_prices')
    op.drop_table('concept_recipes')
    op.drop_table('insumos')
    op.drop_table('concepts')
    op.drop_table('users')
    op.drop_table('locations')
