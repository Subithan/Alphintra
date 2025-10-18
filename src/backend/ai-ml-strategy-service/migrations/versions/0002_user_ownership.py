"""add user ownership columns

Revision ID: 0002
Revises: 0001
Create Date: 2025-10-18 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('user_id', sa.String(), nullable=True))
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.add_column('files', sa.Column('owner_user_id', sa.String(), nullable=True))
    op.create_index('ix_files_owner_user_id', 'files', ['owner_user_id'])


def downgrade() -> None:
    op.drop_index('ix_files_owner_user_id', table_name='files')
    op.drop_column('files', 'owner_user_id')
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_column('projects', 'user_id')

