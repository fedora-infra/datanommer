"""category not null

Revision ID: 5091535d0fb4
Revises: a4f74590bcf
Create Date: 2013-02-23 23:31:48.450673

"""

# revision identifiers, used by Alembic.
revision = '5091535d0fb4'
down_revision = 'a4f74590bcf'

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine


def upgrade():
    engine = create_engine("postgresql+psycopg2://localhost:5432/datanommer")
    conn = engine.connect()

    ctx = MigrationContext.configure(conn)
    op = Operations(ctx)

    op.alter_column("messages", "category", nullable=False)


def downgrade():
    engine = create_engine("postgresql+psycopg2://localhost:5432/datanommer")
    conn = engine.connect()

    ctx = MigrationContext.configure(conn)
    op = Operations(ctx)

    op.alter_column("messages", "category", nullable=True)
