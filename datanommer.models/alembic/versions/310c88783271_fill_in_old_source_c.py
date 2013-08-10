"""fill in old source column data.

Revision ID: 310c88783271
Revises: 4391ce7dc184
Create Date: 2013-08-10 16:36:40.515540

"""

# revision identifiers, used by Alembic.
revision = '310c88783271'
down_revision = '4391ce7dc184'

from alembic import op
import sqlalchemy as sa


def upgrade():
    engine = op.get_bind().engine
    engine.execute("UPDATE messages SET source_name = 'datanommer'")
    engine.execute("UPDATE messages SET source_version = '0'")

def downgrade():
    engine = op.get_bind().engine
    engine.execute("UPDATE messages SET source_name = NULL")
    engine.execute("UPDATE messages SET source_version = NULL")
