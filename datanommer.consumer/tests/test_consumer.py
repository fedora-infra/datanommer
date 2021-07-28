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

import pytest
from fedora_messaging import message

import datanommer.consumer
import datanommer.models


@pytest.fixture
def consumer(mocker):
    mock_get_url = mocker.patch("datanommer.consumer.get_datanommer_sqlalchemy_url")
    mock_get_url.return_value = "sqlite:///fake.db"
    return datanommer.consumer.Nommer()


def test_consume(datanommer_models, consumer):
    example_message = message.Message(
        topic="nice.message", body={"encouragement": "You're doing great!"}
    )

    consumer = datanommer.consumer.Nommer()

    consumer(example_message)
    assert datanommer.models.Message.query.count() == 1


def test_add_exception(datanommer_models, consumer, mocker):
    example_message = message.Message(
        topic="nice.message", body={"encouragement": "You're doing great!"}
    )

    datanommer.models.add = mocker.Mock(side_effect=Exception("an exception"))
    consumer = datanommer.consumer.Nommer()
    with pytest.raises(Exception):
        consumer(example_message)


def test_get_datanommer_sqlalchemy_url_keyerror(mocker):
    mocker.patch.dict(
        datanommer.consumer.config.conf["consumer_config"],
        {},
        clear=True,
    )
    with pytest.raises(ValueError):
        datanommer.consumer.get_datanommer_sqlalchemy_url()
