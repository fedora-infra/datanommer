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
import copy
import unittest
from unittest import mock

from sqlalchemy.orm import scoped_session

import datanommer.consumer
import datanommer.models


filename = ":memory:"


class TestConsumer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import fedmsg.config
        import fedmsg.meta

        config = fedmsg.config.load_config([], None)
        uri = "sqlite:///%s" % filename
        config["datanommer.sqlalchemy.url"] = uri
        config["datanommer.enabled"] = True
        fedmsg.meta.make_processors(**config)
        cls.fedmsg_config = config

    def setUp(self):
        class FakeHub:
            config = self.fedmsg_config

            def subscribe(*args, **kwargs):
                pass

        # We only have to do this so that we can do it over
        # and over again for each test.
        datanommer.models.session = scoped_session(datanommer.models.maker)
        datanommer.models.init(
            self.fedmsg_config["datanommer.sqlalchemy.url"],
            create=True,
        )
        datanommer.consumer.Nommer._initialized = True  # Clearly, a lie.
        self.consumer = datanommer.consumer.Nommer(FakeHub())

    def tearDown(self):
        datanommer.models.session.rollback()
        engine = datanommer.models.session.get_bind()
        datanommer.models.DeclarativeBase.metadata.drop_all(engine)
        datanommer.models._users_seen = set()
        datanommer.models._packages_seen = set()

    def test_duplicate_msg_id(self):
        example_message = dict(
            topic="topic.lol.lol.lol",
            body=dict(
                topic="topic.lol.lol.lol",
                i=1,
                msg_id="1234",
                timestamp=1234,
                msg=dict(
                    foo="bar",
                ),
            ),
        )
        msg1 = copy.deepcopy(example_message)
        msg2 = copy.deepcopy(example_message)

        self.consumer.consume(msg1)
        assert datanommer.models.Message.query.count() == 1

        with mock.patch("fedmsg.publish") as mocked_function:
            # datanommer.models.add() now ignores duplicate messages
            # (messages with the same msg_id).
            self.consumer.consume(msg2)
            assert datanommer.models.Message.query.count() == 1

        mocked_function.assert_not_called()
