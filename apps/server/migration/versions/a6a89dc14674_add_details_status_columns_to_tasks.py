"""add qa_entities_status, relationships_status and topics_status to tasks

Revision ID: a6a89dc14674
Revises: d476c6e01513
Create Date: 2026-09-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a6a89dc14674"
down_revision: Union[str, None] = "d476c6e01513"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("qa_entities_status", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("relationships_status", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("topics_status", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "topics_status")
    op.drop_column("tasks", "relationships_status")
    op.drop_column("tasks", "qa_entities_status")
