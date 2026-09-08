"""add model_name to qa_items, entities, relationships and topics

Revision ID: 58a1a7d19d25
Revises: 9c8b63f3d19e
Create Date: 2026-09-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "58a1a7d19d25"
down_revision: Union[str, None] = "9c8b63f3d19e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("qa_items", sa.Column("model_name", sa.String(), nullable=True))
    op.add_column("entities", sa.Column("model_name", sa.String(), nullable=True))
    op.add_column("relationships", sa.Column("model_name", sa.String(), nullable=True))
    op.add_column("topics", sa.Column("model_name", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("topics", "model_name")
    op.drop_column("relationships", "model_name")
    op.drop_column("entities", "model_name")
    op.drop_column("qa_items", "model_name")
