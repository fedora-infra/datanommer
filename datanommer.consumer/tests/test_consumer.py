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

import pytest

import datanommer.consumer
import datanommer.models


@pytest.fixture
def consumer(fedmsg_config):
    class FakeHub:
        config = fedmsg_config

        def subscribe(*args, **kwargs):
            pass

    datanommer.consumer.Nommer._initialized = True  # Clearly, a lie.
    return datanommer.consumer.Nommer(FakeHub())


def test_duplicate_msg_id(datanommer_models, consumer, mocker):
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

    consumer.consume(msg1)
    assert datanommer.models.Message.query.count() == 1

    mocked_function = mocker.patch("fedmsg.publish")
    # datanommer.models.add() now ignores duplicate messages
    # (messages with the same msg_id).
    consumer.consume(msg2)
    assert datanommer.models.Message.query.count() == 1

    mocked_function.assert_not_called()
