"""add soft delete, audit_log, drop lots_con_usuario view

Revision ID: 003_soft_delete_audit
Revises: 002_add_analyses
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision: str = '003_soft_delete_audit'
down_revision: Union[str, None] = '002_add_analyses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add deleted_at to users
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_users_deleted_at', 'users', ['deleted_at'])
    
    # 2. Add deleted_at to lots
    op.add_column('lots', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_lots_deleted_at', 'lots', ['deleted_at'])
    
    # 3. Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', sa.String(36), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),  # INSERT, UPDATE, DELETE
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_log_table_record', 'audit_log', ['table_name', 'record_id'])
    op.create_index('idx_audit_log_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_created', 'audit_log', ['created_at'])
    
    # 4. Drop lots_con_usuario view (questionable - ORM handles joins)
    op.execute('DROP VIEW IF EXISTS lots_con_usuario')


def downgrade() -> None:
    # Recreate view
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
    
    # Drop audit_log
    op.drop_index('idx_audit_log_created', table_name='audit_log')
    op.drop_index('idx_audit_log_user', table_name='audit_log')
    op.drop_index('idx_audit_log_table_record', table_name='audit_log')
    op.drop_table('audit_log')
    
    # Drop deleted_at from lots
    op.drop_index('idx_lots_deleted_at', table_name='lots')
    op.drop_column('lots', 'deleted_at')
    
    # Drop deleted_at from users
    op.drop_index('idx_users_deleted_at', table_name='users')
    op.drop_column('users', 'deleted_at')