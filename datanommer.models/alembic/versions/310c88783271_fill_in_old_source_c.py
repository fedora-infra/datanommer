# This file is a part of datanommer, a message sink for fedmsg.
# Copyright (C) 2014, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
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
