"""Sesiones de autenticación, versión de credenciales y límites persistentes."""
from alembic import op
import sqlalchemy as sa

revision = "c92ef03a6d10"
down_revision = "b71d8e12a45c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("usuarios", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("usuario_id", sa.String(36), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revocada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expira_en", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_auth_sessions_usuario_id", "auth_sessions", ["usuario_id"])
    with op.batch_alter_table("refresh_tokens") as batch:
        batch.add_column(sa.Column("familia_id", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_refresh_familia", "auth_sessions", ["familia_id"], ["id"])
        batch.create_index("ix_refresh_tokens_familia_id", ["familia_id"])
    # Los tokens anteriores carecen de familia y deben iniciar sesión de nuevo.
    op.execute(sa.text("UPDATE refresh_tokens SET revocado = true"))
    op.create_table(
        "auth_rate_limits",
        sa.Column("clave", sa.String(64), primary_key=True),
        sa.Column("intentos", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("auth_rate_limits")
    with op.batch_alter_table("refresh_tokens") as batch:
        batch.drop_index("ix_refresh_tokens_familia_id")
        batch.drop_constraint("fk_refresh_familia", type_="foreignkey")
        batch.drop_column("familia_id")
    op.drop_table("auth_sessions")
    with op.batch_alter_table("usuarios") as batch:
        batch.drop_column("token_version")
