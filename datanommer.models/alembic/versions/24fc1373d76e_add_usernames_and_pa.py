"""Add usernames and packages columns

Revision ID: 24fc1373d76e
Revises: None
Create Date: 2013-01-04 12:18:38.236047

"""

# revision identifiers, used by Alembic.
revision = '24fc1373d76e'
down_revision = None

from alembic import op
import sqlalchemy as sa

from datanommer.models import models

def upgrade():
    #TODO: Do we want to set a default for the existing logs and make this
    # not nullable?
    for model in models:
        op.add_column(model.__tablename__, sa.Column('usernames',
            sa.UnicodeText)
        )

        op.add_column(model.__tablename__, sa.Column('packages',
            sa.UnicodeText)
        )


def downgrade():
    for model in models:
        op.drop_column(model.__tablename__, 'usernames')
        op.drop_column(model.__tablename__, 'packages')
