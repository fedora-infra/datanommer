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
"""Fix git topics as follows:

git.branch.* => git.branch
git.lookaside.*.new => git.lookaside.new
git.receive.* => git.receive

Data is added to allow the messages to be parsed by the meta. Certificates and
signatures are removed.

There is no downgrade section as this is not a schema change. This revision
cannot be reversed.

Revision ID: 2affa1daa804
Revises: 310c88783271
Create Date: 2013-09-01 10:58:03.127503

"""

# revision identifiers, used by Alembic.
revision = '2affa1daa804'
down_revision = '310c88783271'

from alembic import op
import sqlalchemy as sa

import datanommer.models as m


def upgrade():
    engine = op.get_bind().engine
    m.init(engine=engine)

    # git.branch
    branch = m.Message.topic.like(u'%.git.branch.%')
    for msg in m.Message.query.filter(branch).yield_per(100):
        prefix, suffix = msg.topic.split(u'.git.branch.')
        # Fix topic
        msg.topic = prefix + '.git.branch'
        # Fix message contents
        message = msg.msg
        message['name'] = '.'.join(suffix.split('.')[0:-1])
        message['branch'] = suffix.split('.')[-1]
        msg.msg = message
        # Drop cert and sig
        msg.certificate = None
        msg.signature = None
        m.session.add(msg)

    # git.lookaside.*.new
    lookaside = m.Message.topic.like(u'%.git.lookaside.%.new')
    for msg in m.Message.query.filter(lookaside).yield_per(100):
        prefix, suffix = msg.topic.split(u'.git.lookaside.')
        # Fix topic
        msg.topic = prefix + '.git.lookaside.new'
        # Drop cert and sig
        msg.certificate = None
        msg.signature = None
        m.session.add(msg)

    # git.receive
    receive = m.Message.topic.like(u'%.git.receive.%')
    for msg in m.Message.query.filter(receive).yield_per(100):
        prefix, suffix = msg.topic.split(u'.git.receive.')
        # Fix topic
        msg.topic = prefix + '.git.receive'
        # Fix message contents
        message = msg.msg
        message['commit']['repo'] = '.'.join(suffix.split('.')[0:-1])
        msg.msg = message
        # Drop cert and sig
        msg.certificate = None
        msg.signature = None
        m.session.add(msg)

    m.session.commit()


def downgrade():
    pass
