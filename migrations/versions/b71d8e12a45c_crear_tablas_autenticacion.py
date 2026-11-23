"""crear tablas de autenticacion usuarios y tokens

Revision ID: b71d8e12a45c
Revises: 4629db295117
Create Date: 2026-11-22 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b71d8e12a45c'
down_revision: Union[str, Sequence[str], None] = '4629db295117'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabla usuarios
    op.create_table(
        'usuarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nombre_completo', sa.String(length=150), nullable=False),
        sa.Column('rol', sa.String(length=50), nullable=False),
        sa.Column('activo', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('intentos_fallidos', sa.Integer(), server_default='0', nullable=False),
        sa.Column('bloqueado_hasta', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)
    op.create_index(op.f('ix_usuarios_rol'), 'usuarios', ['rol'], unique=False)

    # 2. Tabla refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('usuario_id', sa.String(length=36), nullable=False),
        sa.Column('expira_en', sa.DateTime(), nullable=False),
        sa.Column('revocado', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_usuario_id'), 'refresh_tokens', ['usuario_id'], unique=False)

    # 3. Tabla password_reset_tokens
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('usuario_id', sa.String(length=36), nullable=False),
        sa.Column('expira_en', sa.DateTime(), nullable=False),
        sa.Column('usado', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_password_reset_tokens_token_hash'), 'password_reset_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_password_reset_tokens_usuario_id'), 'password_reset_tokens', ['usuario_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_password_reset_tokens_usuario_id'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_token_hash'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')

    op.drop_index(op.f('ix_refresh_tokens_usuario_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index(op.f('ix_usuarios_rol'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_email'), table_name='usuarios')
    op.drop_table('usuarios')
