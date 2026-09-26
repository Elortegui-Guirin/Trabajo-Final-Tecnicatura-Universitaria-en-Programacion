"""add analyses table

Revision ID: 002_add_analyses
Revises: 001_initial_schema
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_analyses'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    resourcetype_enum = sa.Enum('resource_1', 'resource_2', 'resource_3', 'resource_4', name='resourcetype')
    analysisstatus_enum = sa.Enum('pending', 'processing', 'completed', 'failed', name='analysisstatus')
    resourcetype_enum.create(op.get_bind(), checkfirst=True)
    analysisstatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('lot_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('resource_type', resourcetype_enum, nullable=False),
        sa.Column('average_rate', sa.Numeric(10, 4), nullable=False),
        sa.Column('min_value', sa.Numeric(10, 4), nullable=True),
        sa.Column('max_value', sa.Numeric(10, 4), nullable=True),
        sa.Column('std_dev', sa.Numeric(10, 4), nullable=True),
        sa.Column('percentiles', sa.JSON(), nullable=True),
        sa.Column('raster_file_reference', sa.String(500), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', analysisstatus_enum, nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lot_id'], ['lots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('idx_analyses_lot_id', 'analyses', ['lot_id'])
    op.create_index('idx_analyses_resource_type', 'analyses', ['resource_type'])
    op.create_index('idx_analyses_status', 'analyses', ['status'])
    op.create_index('idx_analyses_lot_resource', 'analyses', ['lot_id', 'resource_type'])


def downgrade() -> None:
    op.drop_index('idx_analyses_lot_resource', table_name='analyses')
    op.drop_index('idx_analyses_status', table_name='analyses')
    op.drop_index('idx_analyses_resource_type', table_name='analyses')
    op.drop_index('idx_analyses_lot_id', table_name='analyses')
    op.drop_table('analyses')
    
    # Drop ENUMs
    sa.Enum(name='analysisstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='resourcetype').drop(op.get_bind(), checkfirst=True)