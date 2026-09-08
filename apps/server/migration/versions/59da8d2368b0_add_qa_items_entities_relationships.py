"""add qa_items, entities and relationships tables

Revision ID: 59da8d2368b0
Revises: 6fdb21e394c9
Create Date: 2026-09-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "59da8d2368b0"
down_revision: Union[str, None] = "6fdb21e394c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "qa_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_qa_items_task_id"), "qa_items", ["task_id"], unique=False)
    op.create_index(op.f("ix_qa_items_chunk_index"), "qa_items", ["chunk_index"], unique=False)

    op.create_table(
        "entities",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("contexts", sa.JSON(), nullable=True),
        sa.Column("pages", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_entities_task_id"), "entities", ["task_id"], unique=False)
    op.create_index(op.f("ix_entities_chunk_index"), "entities", ["chunk_index"], unique=False)

    op.create_table(
        "relationships",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=True),
        sa.Column("source_entity_id", sa.String(), nullable=False),
        sa.Column("target_entity_id", sa.String(), nullable=False),
        sa.Column("relationship_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_relationships_task_id"), "relationships", ["task_id"], unique=False)
    op.create_index(op.f("ix_relationships_chunk_index"), "relationships", ["chunk_index"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_relationships_chunk_index"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_task_id"), table_name="relationships")
    op.drop_table("relationships")

    op.drop_index(op.f("ix_entities_chunk_index"), table_name="entities")
    op.drop_index(op.f("ix_entities_task_id"), table_name="entities")
    op.drop_table("entities")

    op.drop_index(op.f("ix_qa_items_chunk_index"), table_name="qa_items")
    op.drop_index(op.f("ix_qa_items_task_id"), table_name="qa_items")
    op.drop_table("qa_items")
