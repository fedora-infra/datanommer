"""category not null

Revision ID: 5091535d0fb4
Revises: a4f74590bcf
Create Date: 2013-02-23 23:31:48.450673

"""

# revision identifiers, used by Alembic.
revision = '5091535d0fb4'
down_revision = 'a4f74590bcf'

from alembic import op


def upgrade():
    op.alter_column("messages", "category", nullable=False)


def downgrade():
    op.alter_column("messages", "category", nullable=True)
