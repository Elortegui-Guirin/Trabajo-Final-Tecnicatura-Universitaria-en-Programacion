"""add analysis improvements: raster versioning, cache, storage policy

Revision ID: 006_analysis_improvements
Revises: 005_lot_versions
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_analysis_improvements'
down_revision: Union[str, None] = '005_lot_versions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to analyses table
    op.add_column('analyses', sa.Column('raster_version', sa.String(100), nullable=False, server_default='v1.0.0'))
    op.add_column('analyses', sa.Column('raster_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('analyses', sa.Column('clipped_raster_path', sa.Text(), nullable=True))
    op.add_column('analyses', sa.Column('store_clipped_raster', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('analyses', sa.Column('lot_geometry_hash', sa.String(64), nullable=False, server_default=''))
    
    # Create indexes for new columns
    op.create_index('idx_analyses_lot_resource_status', 'analyses', ['lot_id', 'resource_type', 'status'])
    op.create_index('idx_analyses_geometry_hash', 'analyses', ['lot_geometry_hash'])
    op.create_index('idx_analyses_raster_version', 'analyses', ['raster_version'])


def downgrade() -> None:
    op.drop_index('idx_analyses_raster_version', table_name='analyses')
    op.drop_index('idx_analyses_geometry_hash', table_name='analyses')
    op.drop_index('idx_analyses_lot_resource_status', table_name='analyses')
    op.drop_column('analyses', 'lot_geometry_hash')
    op.drop_column('analyses', 'store_clipped_raster')
    op.drop_column('analyses', 'clipped_raster_path')
    op.drop_column('analyses', 'raster_date')
    op.drop_column('analyses', 'raster_version')