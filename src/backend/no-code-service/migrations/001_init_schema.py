"""Initialize no-code service database schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_uuid'), 'users', ['uuid'], unique=False)

    # Create nocode_workflows table
    op.create_table('nocode_workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('workflow_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('generated_code', sa.Text(), nullable=True),
        sa.Column('generated_code_language', sa.String(length=20), nullable=True),
        sa.Column('generated_requirements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('generated_code_size', sa.Integer(), nullable=True),
        sa.Column('generated_code_lines', sa.Integer(), nullable=True),
        sa.Column('compiler_version', sa.String(length=50), nullable=True),
        sa.Column('compilation_status', sa.String(length=20), nullable=True),
        sa.Column('compilation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('deployment_status', sa.String(length=20), nullable=True),
        sa.Column('execution_mode', sa.String(length=20), nullable=True),
        sa.Column('execution_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('aiml_training_job_id', sa.String(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('parent_workflow_id', sa.Integer(), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('total_executions', sa.Integer(), nullable=True),
        sa.Column('successful_executions', sa.Integer(), nullable=True),
        sa.Column('avg_performance_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_workflow_id'], ['nocode_workflows.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_nocode_workflows_category'), 'nocode_workflows', ['category'], unique=False)
    op.create_index(op.f('ix_nocode_workflows_id'), 'nocode_workflows', ['id'], unique=False)
    op.create_index(op.f('ix_nocode_workflows_user_id'), 'nocode_workflows', ['user_id'], unique=False)
    op.create_index(op.f('ix_nocode_workflows_uuid'), 'nocode_workflows', ['uuid'], unique=False)

    # Create nocode_components table
    op.create_table('nocode_components',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('subcategory', sa.String(length=50), nullable=True),
        sa.Column('component_type', sa.String(length=50), nullable=False),
        sa.Column('input_schema', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('output_schema', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('parameters_schema', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('default_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('code_template', sa.Text(), nullable=False),
        sa.Column('imports_required', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('dependencies', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('ui_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_nocode_components_category'), 'nocode_components', ['category'], unique=False)
    op.create_index(op.f('ix_nocode_components_id'), 'nocode_components', ['id'], unique=False)
    op.create_index(op.f('ix_nocode_components_uuid'), 'nocode_components', ['uuid'], unique=False)

    # Create nocode_templates table
    op.create_table('nocode_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('difficulty_level', sa.String(length=20), nullable=True),
        sa.Column('template_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('preview_image_url', sa.String(length=500), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('estimated_time_minutes', sa.Integer(), nullable=True),
        sa.Column('expected_performance', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_nocode_templates_category'), 'nocode_templates', ['category'], unique=False)
    op.create_index(op.f('ix_nocode_templates_id'), 'nocode_templates', ['id'], unique=False)
    op.create_index(op.f('ix_nocode_templates_uuid'), 'nocode_templates', ['uuid'], unique=False)

    # Create nocode_executions table
    op.create_table('nocode_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('execution_type', sa.String(length=20), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('symbols', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('initial_capital', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('current_step', sa.String(length=255), nullable=True),
        sa.Column('final_capital', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('total_return', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('total_return_percent', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('sharpe_ratio', sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column('max_drawdown_percent', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('winning_trades', sa.Integer(), nullable=True),
        sa.Column('trades_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_logs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_logs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['nocode_workflows.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_nocode_executions_id'), 'nocode_executions', ['id'], unique=False)
    op.create_index(op.f('ix_nocode_executions_status'), 'nocode_executions', ['status'], unique=False)
    op.create_index(op.f('ix_nocode_executions_user_id'), 'nocode_executions', ['user_id'], unique=False)
    op.create_index(op.f('ix_nocode_executions_uuid'), 'nocode_executions', ['uuid'], unique=False)
    op.create_index(op.f('ix_nocode_executions_workflow_id'), 'nocode_executions', ['workflow_id'], unique=False)

    # Create compilation_results table
    op.create_table('compilation_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('python_code', sa.Text(), nullable=False),
        sa.Column('validation_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['nocode_workflows.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_compilation_results_user_id', 'compilation_results', ['user_id'], unique=False)

    # Create execution_history table
    op.create_table('execution_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('execution_mode', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('execution_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_logs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_code', sa.Text(), nullable=True),
        sa.Column('generated_requirements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('compilation_stats', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['nocode_workflows.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index('ix_execution_history_user_id', 'execution_history', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_index('ix_execution_history_user_id', table_name='execution_history')
    op.drop_table('execution_history')
    op.drop_index('ix_compilation_results_user_id', table_name='compilation_results')
    op.drop_table('compilation_results')
    op.drop_index(op.f('ix_nocode_executions_workflow_id'), table_name='nocode_executions')
    op.drop_index(op.f('ix_nocode_executions_uuid'), table_name='nocode_executions')
    op.drop_index(op.f('ix_nocode_executions_user_id'), table_name='nocode_executions')
    op.drop_index(op.f('ix_nocode_executions_status'), table_name='nocode_executions')
    op.drop_index(op.f('ix_nocode_executions_id'), table_name='nocode_executions')
    op.drop_table('nocode_executions')
    op.drop_index(op.f('ix_nocode_templates_uuid'), table_name='nocode_templates')
    op.drop_index(op.f('ix_nocode_templates_id'), table_name='nocode_templates')
    op.drop_index(op.f('ix_nocode_templates_category'), table_name='nocode_templates')
    op.drop_table('nocode_templates')
    op.drop_index(op.f('ix_nocode_components_uuid'), table_name='nocode_components')
    op.drop_index(op.f('ix_nocode_components_id'), table_name='nocode_components')
    op.drop_index(op.f('ix_nocode_components_category'), table_name='nocode_components')
    op.drop_table('nocode_components')
    op.drop_index(op.f('ix_nocode_workflows_uuid'), table_name='nocode_workflows')
    op.drop_index(op.f('ix_nocode_workflows_user_id'), table_name='nocode_workflows')
    op.drop_index(op.f('ix_nocode_workflows_id'), table_name='nocode_workflows')
    op.drop_index(op.f('ix_nocode_workflows_category'), table_name='nocode_workflows')
    op.drop_table('nocode_workflows')
    op.drop_index(op.f('ix_users_uuid'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')