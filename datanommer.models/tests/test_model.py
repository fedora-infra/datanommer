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
import json
import logging

import pytest
from bodhi.messages.schemas.update import UpdateCommentV1
from fedora_messaging import message as fedora_message
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.query import Query

from datanommer.models import add, init, Message, Package, session, User


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


def test_init_uri_and_engine():
    uri = "sqlite:///db.db"
    engine = create_engine(uri)

    with pytest.raises(ValueError, match="uri and engine cannot both be specified"):
        init(uri, engine=engine)


def test_init_no_uri_and_no_engine():
    with pytest.raises(ValueError, match="One of uri or engine must be specified"):
        init()


def test_init_with_engine(caplog):
    uri = "sqlite:///db.db"
    engine = create_engine(uri)

    init(engine=engine)

    assert not caplog.records

    # if the init with just the engine worked, trying it again will fail
    init(engine=engine)
    assert caplog.records[0].message == "Session already initialized.  Bailing"


def test_init_no_init_twice(datanommer_models, mocker, caplog):
    init("sqlite:///db.db")
    assert caplog.records[0].message == "Session already initialized.  Bailing"


def test_unclassified_category(datanommer_models):
    example_message = generate_message(topic="too.short")
    add(example_message)
    dbmsg = Message.query.first()

    assert dbmsg.category == "Unclassified"


def test_from_msg_id(datanommer_models):
    example_message = generate_message()
    example_message.id = "ACUSTOMMESSAGEID"
    add(example_message)
    dbmsg = Message.from_msg_id("ACUSTOMMESSAGEID")

    assert dbmsg.msg_id == "ACUSTOMMESSAGEID"


def test_add_missing_msg_id(datanommer_models, caplog):
    caplog.set_level(logging.INFO)
    example_message = generate_message()
    example_message._properties.message_id = None
    add(example_message)
    dbmsg = Message.query.first()
    assert (
        "Message on org.fedoraproject.test.a.nice.message was received without a msg_id"
        in caplog.records[-1].message
    )
    assert dbmsg.msg_id is not None


def test_add_missing_timestamp(datanommer_models):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = None

    add(example_message)

    dbmsg = Message.query.first()
    timediff = datetime.datetime.utcnow() - dbmsg.timestamp
    # 10 seconds between adding the message and checking
    # the timestamp should be more than enough.
    assert timediff < datetime.timedelta(seconds=10)


def test_add_timestamp_with_Z(datanommer_models):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = "2021-07-27T04:22:42Z"

    add(example_message)

    dbmsg = Message.query.first()
    assert dbmsg.timestamp.astimezone(datetime.timezone.utc) == datetime.datetime(
        2021, 7, 27, 4, 22, 42, tzinfo=datetime.timezone.utc
    )


def test_add_timestamp_with_junk(datanommer_models, caplog):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = "2021-07-27T04:22:42JUNK"

    add(example_message)

    assert "Failed to parse sent-at timestamp value" in caplog.records[0].message

    assert Message.query.count() == 0


def test_add_and_check_for_others(datanommer_models):

    # There are no users or packages at the start
    assert User.query.count() == 0
    assert Package.query.count() == 0

    # Then add a message
    add(generate_bodhi_update_complete_message())

    # There should now be two of each
    assert User.query.count() == 2
    assert Package.query.count() == 2

    # If we add it again, there should be no duplicates
    add(generate_bodhi_update_complete_message())
    assert User.query.count() == 2
    assert Package.query.count() == 2

    # Add a new username
    add(generate_bodhi_update_complete_message(text="this is @abompard in a comment"))
    assert User.query.count() == 3
    assert Package.query.count() == 2


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


def test_grep_start_end_validation(datanommer_models):
    with pytest.raises(
        ValueError,
        match="Either both start and end must be specified or neither must be specified",
    ):
        Message.grep(start="2020-03-26")
    with pytest.raises(
        ValueError,
        match="Either both start and end must be specified or neither must be specified",
    ):
        Message.grep(end="2020-03-26")


def test_grep_start_end(datanommer_models):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = "2021-04-01T00:00:01"
    add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    bodhi_example_message._properties.headers["sent-at"] = "2021-06-01T00:00:01"
    add(bodhi_example_message)

    session.flush()
    total, pages, messages = Message.grep(start="2021-04-01", end="2021-05-01")
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == example_message.body

    total, pages, messages = Message.grep(start="2021-06-01", end="2021-07-01")
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == bodhi_example_message.body


def test_grep_msg_id(datanommer_models):
    example_message = generate_message()
    add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    add(bodhi_example_message)

    session.flush()
    total, pages, messages = Message.grep(msg_id=example_message.id)
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == example_message.body

    total, pages, messages = Message.grep(msg_id=bodhi_example_message.id)
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == bodhi_example_message.body

    total, pages, messages = Message.grep(msg_id="NOTAMESSAGEID")
    assert total == 0
    assert pages == 0
    assert len(messages) == 0


def test_grep_users(datanommer_models):
    example_message = generate_message()
    add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    add(bodhi_example_message)

    session.flush()

    total, pages, messages = Message.grep(users=["dudemcpants"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == bodhi_example_message.body


def test_grep_not_users(datanommer_models):
    example_message = generate_message()
    add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    add(bodhi_example_message)

    session.flush()

    total, pages, messages = Message.grep(not_users=["dudemcpants"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == example_message.body


def test_grep_packages(datanommer_models):
    example_message = generate_message()
    add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    add(bodhi_example_message)

    session.flush()

    total, pages, messages = Message.grep(packages=["kernel"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == bodhi_example_message.body


def test_grep_not_packages(datanommer_models):
    example_message = generate_message()
    add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    add(bodhi_example_message)

    session.flush()

    total, pages, messages = Message.grep(not_packages=["kernel"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == example_message.body


def test_grep_contains(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    add(example_message)
    session.flush()
    t, p, r = Message.grep(contains=["doing"])
    assert t == 1
    assert p == 1
    assert len(r) == 1
    assert r[0].msg == example_message.body


def test_grep_rows_per_page_none(datanommer_models):
    for x in range(0, 200):
        example_message = generate_message()
        example_message.id = f"{x}"
        add(example_message)

    session.flush()

    total, pages, messages = Message.grep()
    assert total == 200
    assert pages == 2
    assert len(messages) == 100

    total, pages, messages = Message.grep(rows_per_page=None)
    assert total == 200
    assert pages == 1
    assert len(messages) == 200


def test_grep_rows_per_page_zero(datanommer_models):
    for x in range(0, 200):
        example_message = generate_message()
        example_message.id = f"{x}"
        add(example_message)
    session.flush()

    try:
        total, pages, messages = Message.grep(rows_per_page=0)
    except ZeroDivisionError as e:
        assert False, e
    assert total == 200
    assert pages == 1
    assert len(messages) == 200


def test_grep_defer(datanommer_models):
    example_message = generate_message()
    add(example_message)

    session.flush()

    total, pages, query = Message.grep(defer=True)
    assert isinstance(query, Query)

    assert query.all() == Message.grep()[2]


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


def test_add_duplicate_package(datanommer_models):
    # Define a special message schema and register it
    class MessageWithPackages(fedora_message.Message):
        @property
        def packages(self):
            return ["pkg", "pkg"]

    fedora_message._schema_name_to_class["MessageWithPackages"] = MessageWithPackages
    fedora_message._class_to_schema_name[MessageWithPackages] = "MessageWithPackages"
    example_message = MessageWithPackages(
        topic="org.fedoraproject.test.a.nice.message",
        body={"encouragement": "You're doing great!"},
        headers=None,
    )
    try:
        add(example_message)
    except IntegrityError as e:
        assert False, e
    assert Message.query.count() == 1
    dbmsg = Message.query.first()
    assert len(dbmsg.packages) == 1
    assert dbmsg.packages[0].name == "pkg"


def test_add_message_with_error_on_packages(datanommer_models, caplog):
    # Define a special message schema and register it
    class CustomMessage(fedora_message.Message):
        @property
        def packages(self):
            raise KeyError

        def _filter_headers(self):
            return {}

    fedora_message._schema_name_to_class["CustomMessage"] = CustomMessage
    fedora_message._class_to_schema_name[CustomMessage] = "CustomMessage"
    example_message = CustomMessage(
        topic="org.fedoraproject.test.a.nice.message",
        body={"encouragement": "You're doing great!"},
        headers=None,
    )
    try:
        add(example_message)
    except KeyError as e:
        assert False, e
    assert Message.query.count() == 1
    assert caplog.records[0].message == (
        f"Could not get the list of packages from a message on "
        f"org.fedoraproject.test.a.nice.message with id {example_message.id}"
    )


def test_as_fedora_message_dict(datanommer_models):
    example_message = generate_message()
    add(example_message)

    dbmsg = Message.query.first()

    message_json = json.dumps(dbmsg.as_fedora_message_dict())

    # this should be the same as if we use the fedora_messaging dump function
    assert json.loads(fedora_message.dumps(example_message)) == json.loads(message_json)


def test_as_fedora_message_dict_old_headers(datanommer_models):
    # Messages received with fedmsg don't have the sent-at header
    example_message = generate_message()
    add(example_message)

    dbmsg = Message.query.first()
    del dbmsg.headers["sent-at"]

    message_dict = dbmsg.as_fedora_message_dict()
    print(message_dict)
    print(json.loads(fedora_message.dumps(example_message)))

    # this should be the same as if we use the fedora_messaging dump function
    assert json.loads(fedora_message.dumps(example_message)) == message_dict


def test_as_fedora_message_dict_no_headers(datanommer_models):
    # Messages can have no headers
    example_message = generate_message()
    add(example_message)

    dbmsg = Message.query.first()
    assert len(dbmsg.headers.keys()) == 3

    # Clear the headers
    dbmsg.headers = None

    try:
        message_dict = dbmsg.as_fedora_message_dict()
    except TypeError as e:
        assert False, e

    assert list(message_dict["headers"].keys()) == ["sent-at"]


def test_as_dict(datanommer_models):
    add(generate_message())
    dbmsg = Message.query.first()
    message_dict = dbmsg.as_dict()

    # we should have 14 keys in this dict
    assert len(message_dict) == 14
    assert message_dict["msg"] == {"encouragement": "You're doing great!"}
    assert message_dict["topic"] == "org.fedoraproject.test.a.nice.message"


def test_as_dict_with_users_and_packages(datanommer_models):
    add(generate_bodhi_update_complete_message())
    dbmsg = Message.query.first()
    message_dict = dbmsg.as_dict()

    assert message_dict["users"] == ["dudemcpants", "ryanlerch"]
    assert message_dict["packages"] == ["abrt-addon-python3", "kernel"]


def test___json__deprecated(datanommer_models, caplog, mocker):
    mock_as_dict = mocker.patch("datanommer.models.Message.as_dict")

    add(generate_message())

    with pytest.warns(DeprecationWarning):
        Message.query.first().__json__()

    mock_as_dict.assert_called_once()


def test_singleton_create(datanommer_models):
    Package.get_or_create("foobar")
    assert [p.name for p in Package.query.all()] == ["foobar"]


def test_singleton_get_existing(datanommer_models):
    p1 = Package.get_or_create("foobar")
    # Clear the in-memory cache
    Package._cache.clear()
    p2 = Package.get_or_create("foobar")
    assert p1.id == p2.id
