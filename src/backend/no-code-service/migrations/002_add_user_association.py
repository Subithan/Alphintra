"""Add user association to CompilationResult and ExecutionHistory tables.

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user_id columns to missing tables."""

    # Add user_id to compilation_results table
    op.add_column('compilation_results',
        sa.Column('user_id', sa.Integer(), nullable=True, index=True)
    )

    # Add foreign key constraint for compilation_results.user_id
    op.create_foreign_key(
        'fk_compilation_results_user_id',
        'compilation_results', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add user_id to execution_history table
    op.add_column('execution_history',
        sa.Column('user_id', sa.Integer(), nullable=True, index=True)
    )

    # Add foreign key constraint for execution_history.user_id
    op.create_foreign_key(
        'fk_execution_history_user_id',
        'execution_history', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create indexes for performance
    op.create_index('ix_compilation_results_user_id', 'compilation_results', ['user_id'])
    op.create_index('ix_execution_history_user_id', 'execution_history', ['user_id'])


def downgrade() -> None:
    """Remove user_id columns and constraints."""

    # Drop indexes
    op.drop_index('ix_compilation_results_user_id', table_name='compilation_results')
    op.drop_index('ix_execution_history_user_id', table_name='execution_history')

    # Drop foreign key constraints
    op.drop_constraint('fk_compilation_results_user_id', table_name='compilation_results', type_='foreignkey')
    op.drop_constraint('fk_execution_history_user_id', table_name='execution_history', type_='foreignkey')

    # Drop user_id columns
    op.drop_column('execution_history', 'user_id')
    op.drop_column('compilation_results', 'user_id')