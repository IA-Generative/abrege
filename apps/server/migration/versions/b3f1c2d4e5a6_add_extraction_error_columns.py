"""add qa_entities_error, relationships_error and topics_error to tasks

Revision ID: b3f1c2d4e5a6
Revises: a6a89dc14674
Create Date: 2026-10-06 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f1c2d4e5a6"
down_revision: Union[str, None] = "a6a89dc14674"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("qa_entities_error", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("relationships_error", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("topics_error", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "topics_error")
    op.drop_column("tasks", "relationships_error")
    op.drop_column("tasks", "qa_entities_error")
