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
"""Add msg_id column

Revision ID: 143ec484f5ba
Revises: 2affa1daa804
Create Date: 2013-09-05 21:34:12.915709

"""

# revision identifiers, used by Alembic.
revision = '143ec484f5ba'
down_revision = '2affa1daa804'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('messages', sa.Column('msg_id', sa.UnicodeText, nullable=True,
                                        unique=True, default=None))
    pass


def downgrade():
    op.drop_column('messages', 'msg_id')
    pass
