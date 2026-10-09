"""add lot_versions table for geometry history

Revision ID: 005_lot_versions
Revises: 004_auth_improvements
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_lot_versions'
down_revision: Union[str, None] = '004_auth_improvements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lot_versions table
    op.create_table(
        'lot_versions',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('lot_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('area_ha', sa.Numeric(10, 4), nullable=False),
        sa.Column('geometry', postgresql.GEOMETRY(geometry_type='POLYGON', srid=4326), nullable=False),
        sa.Column('changed_by', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('change_reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lot_id'], ['lots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('idx_lot_versions_lot_id', 'lot_versions', ['lot_id'])
    op.create_index('idx_lot_versions_version', 'lot_versions', ['lot_id', 'version_number'])
    op.create_index('idx_lot_versions_changed_by', 'lot_versions', ['changed_by'])
    op.create_index('idx_lot_versions_created', 'lot_versions', ['created_at'])
    
    # Unique constraint: one version number per lot
    op.create_unique_constraint('uq_lot_versions_lot_version', 'lot_versions', ['lot_id', 'version_number'])


def downgrade() -> None:
    op.drop_constraint('uq_lot_versions_lot_version', table_name='lot_versions')
    op.drop_index('idx_lot_versions_created', table_name='lot_versions')
    op.drop_index('idx_lot_versions_changed_by', table_name='lot_versions')
    op.drop_index('idx_lot_versions_version', table_name='lot_versions')
    op.drop_index('idx_lot_versions_lot_id', table_name='lot_versions')
    op.drop_table('lot_versions')