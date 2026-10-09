"""add auth improvements: email verification, password reset, login attempts

Revision ID: 004_auth_improvements
Revises: 003_soft_delete_audit
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision: str = '004_auth_improvements'
down_revision: Union[str, None] = '003_soft_delete_audit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email verification fields
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_users_verification_token', 'users', ['verification_token'])
    
    # Add password reset fields
    op.add_column('users', sa.Column('reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_users_reset_token', 'users', ['reset_token'])
    
    # Add login attempt control fields
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_users_locked_until', 'users', ['locked_until'])


def downgrade() -> None:
    op.drop_index('idx_users_locked_until', table_name='users')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    
    op.drop_index('idx_users_reset_token', table_name='users')
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')
    
    op.drop_index('idx_users_verification_token', table_name='users')
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'email_verified')