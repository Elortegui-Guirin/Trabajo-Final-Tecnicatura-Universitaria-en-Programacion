"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('verification_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reset_token', sa.String(255), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'])
    op.create_index('ix_users_verification_token', 'users', ['verification_token'])
    op.create_index('ix_users_reset_token', 'users', ['reset_token'])
    op.create_index('ix_users_locked_until', 'users', ['locked_until'])
    
    # Create lots table
    op.create_table(
        'lots',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('area_ha', sa.Numeric(10, 4), nullable=False),
        sa.Column('geometry', postgresql.GEOMETRY(geometry_type='POLYGON', srid=4326), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_lots_user_id', 'lots', ['user_id'])
    op.create_index('idx_lots_deleted_at', 'lots', ['deleted_at'])
    op.create_index('idx_lots_geometry', 'lots', ['geometry'], postgresql_using='gist')
    
    # Create lots_con_usuario view
    op.execute('''
        CREATE VIEW lots_con_usuario AS
        SELECT
            l.id,
            l.user_id,
            u.email AS user_email,
            u.full_name AS user_name,
            l.name,
            l.area_ha,
            l.geometry,
            l.created_at,
            l.updated_at
        FROM lots l
        JOIN users u ON l.user_id = u.id
    ''')
    
    # Trigger function for updated_at
    op.execute('''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Triggers for updated_at
    op.execute("CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER update_lots_updated_at BEFORE UPDATE ON lots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_lots_updated_at ON lots;")
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column;")
    op.execute("DROP VIEW IF EXISTS lots_con_usuario;")
    op.drop_index('idx_lots_geometry', table_name='lots')
    op.drop_index('idx_lots_deleted_at', table_name='lots')
    op.drop_index('idx_lots_user_id', table_name='lots')
    op.drop_table('lots')
    op.drop_index('ix_users_locked_until', table_name='users')
    op.drop_index('ix_users_reset_token', table_name='users')
    op.drop_index('ix_users_verification_token', table_name='users')
    op.drop_index('ix_users_deleted_at', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS postgis;')