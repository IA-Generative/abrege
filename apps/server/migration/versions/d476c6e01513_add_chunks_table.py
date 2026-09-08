"""add chunks table

Revision ID: d476c6e01513
Revises: 58a1a7d19d25
Create Date: 2026-09-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d476c6e01513"
down_revision: Union[str, None] = "58a1a7d19d25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "chunks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chunks_task_id"), "chunks", ["task_id"], unique=False)
    op.create_index(op.f("ix_chunks_chunk_index"), "chunks", ["chunk_index"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_chunks_chunk_index"), table_name="chunks")
    op.drop_index(op.f("ix_chunks_task_id"), table_name="chunks")
    op.drop_table("chunks")
