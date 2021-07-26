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
import datetime

from bodhi.messages.schemas.update import UpdateCommentV1
from fedora_messaging import message as fedora_message
from sqlalchemy.exc import IntegrityError

from datanommer.models import add, Message, session


def generate_message(
    topic="org.fedoraproject.test.a.nice.message",
    body={"encouragement": "You're doing great!"},
    headers=None,
):
    return fedora_message.Message(topic=topic, body=body, headers=headers)


def generate_bodhi_update_complete_message(text="testing testing"):
    msg = UpdateCommentV1(
        body={
            "comment": {
                "karma": -1,
                "text": text,
                "timestamp": "2019-03-18 16:54:48",
                "update": {
                    "alias": "FEDORA-EPEL-2021-f2d195dada",
                    "builds": [
                        {"nvr": "abrt-addon-python3-2.1.11-50.el7"},
                        {"nvr": "kernel-10.4.0-2.el7"},
                    ],
                    "status": "pending",
                    "release": {"name": "F35"},
                    "request": "testing",
                    "user": {"name": "ryanlerch"},
                },
                "user": {"name": "dudemcpants"},
            }
        }
    )
    msg.topic = f"org.fedoraproject.stg.{msg.topic}"
    return msg


def test_add_missing_timestamp(datanommer_models):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = None

    add(example_message)

    dbmsg = Message.query.first()
    timediff = datetime.datetime.utcnow() - dbmsg.timestamp
    # 10 seconds between adding the message and checking
    # the timestamp should be more than enough.
    assert timediff < datetime.timedelta(seconds=10)


def test_add_and_check_for_others(datanommer_models):
    def _count_array_attr(name):
        return Message.get_array(name).count()

    # There are no users or packages at the start
    assert _count_array_attr("users") == 0
    assert _count_array_attr("packages") == 0

    # Then add a message
    add(generate_bodhi_update_complete_message())

    # There should now be two of each
    assert _count_array_attr("users") == 2
    assert _count_array_attr("packages") == 2

    # If we add it again, there should be no duplicates
    add(generate_bodhi_update_complete_message())
    assert _count_array_attr("users") == 2
    assert _count_array_attr("packages") == 2

    # Add a new username
    add(generate_bodhi_update_complete_message(text="this is @abompard in a comment"))
    assert _count_array_attr("users") == 3
    assert _count_array_attr("packages") == 2


def test_add_nothing(datanommer_models):
    assert Message.query.count() == 0


def test_add_and_check(datanommer_models):
    add(generate_message())
    session.flush()
    assert Message.query.count() == 1


def test_categories(datanommer_models):
    add(generate_bodhi_update_complete_message())
    session.flush()
    obj = Message.query.first()
    assert obj.category == "bodhi"


def test_categories_with_umb(datanommer_models):
    add(generate_message(topic="/topic/VirtualTopic.eng.brew.task.closed"))
    session.flush()
    obj = Message.query.first()
    assert obj.category == "brew"


def test_grep_all(datanommer_models):
    example_message = generate_message()
    add(example_message)
    session.flush()
    t, p, r = Message.grep()
    assert t == 1
    assert p == 1
    assert len(r) == 1
    assert r[0].msg == example_message.body


def test_grep_category(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    add(example_message)
    session.flush()
    t, p, r = Message.grep(categories=["bodhi"])
    assert t == 1
    assert p == 1
    assert len(r) == 1
    assert r[0].msg == example_message.body


def test_grep_not_category(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    add(example_message)
    session.flush()
    t, p, r = Message.grep(not_categories=["bodhi"])
    assert t == 0
    assert p == 0
    assert len(r) == 0


def test_add_headers(datanommer_models):
    example_headers = {"foo": "bar", "baz": 1, "wibble": ["zork", "zap"]}
    example_message = generate_message(
        topic="org.fedoraproject.prod.bodhi.newupdate", headers=example_headers
    )
    add(example_message)
    dbmsg = Message.query.first()
    assert dbmsg.headers["foo"] == "bar"
    assert dbmsg.headers["baz"] == 1
    assert dbmsg.headers["wibble"] == ["zork", "zap"]


def test_grep_topics(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    add(example_message)
    session.flush()
    t, p, r = Message.grep(topics=["org.fedoraproject.prod.bodhi.newupdate"])
    assert t == 1
    assert p == 1
    assert len(r) == 1
    assert r[0].msg == example_message.body


def test_grep_not_topics(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    add(example_message)
    session.flush()
    t, p, r = Message.grep(not_topics=["org.fedoraproject.prod.bodhi.newupdate"])
    assert t == 0
    assert p == 0
    assert len(r) == 0


def test_add_duplicate(datanommer_models, caplog):
    example_message = generate_message()
    add(example_message)
    add(example_message)
    # if no exception was thrown, then we successfully ignored the
    # duplicate message
    assert Message.query.count() == 1
    assert (
        "Skipping message from org.fedoraproject.test.a.nice.message"
        in caplog.records[0].message
    )


def test_add_integrity_error(datanommer_models, mocker, caplog):
    mock_session_add = mocker.patch("datanommer.models.session.add")
    mock_session_add.side_effect = IntegrityError("asdf", "asd", "asdas")
    example_message = generate_message()
    add(example_message)
    assert "Unknown Integrity Error: message" in caplog.records[0].message
    assert Message.query.count() == 0
