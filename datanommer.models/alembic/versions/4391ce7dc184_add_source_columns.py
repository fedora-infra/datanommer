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
"""add source columns

Revision ID: 4391ce7dc184
Revises: 1d4feffd78fe
Create Date: 2013-08-10 16:32:39.466582

"""

# revision identifiers, used by Alembic.
revision = '4391ce7dc184'
down_revision = '1d4feffd78fe'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('messages', sa.Column('source_name', sa.UnicodeText))
    op.add_column('messages', sa.Column('source_version', sa.UnicodeText))


def downgrade():
    op.drop_column('messages', 'source_name')
    op.drop_column('messages', 'source_version')
