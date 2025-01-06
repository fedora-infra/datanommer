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
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.selectable import Select

import datanommer.models as dm


def generate_message(
    topic="org.fedoraproject.test.a.nice.message",
    body=None,
    headers=None,
):
    body = body or {"encouragement": "You're doing great!"}
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


@pytest.fixture
def add_200_messages(datanommer_models):
    for x in range(0, 200):
        example_message = generate_message()
        example_message.id = f"{x}"
        dm.add(example_message)
    dm.session.flush()


def test_init_uri_and_engine():
    uri = "sqlite:///db.db"
    engine = create_engine(uri, future=True)

    with pytest.raises(ValueError, match="uri and engine cannot both be specified"):
        dm.init(uri, engine=engine)


def test_init_no_uri_and_no_engine():
    with pytest.raises(ValueError, match="One of uri or engine must be specified"):
        dm.init()


def test_init_with_engine(caplog):
    uri = "sqlite:///db.db"
    engine = create_engine(uri, future=True)

    dm.init(engine=engine)

    assert not caplog.records

    # if the init with just the engine worked, trying it again will fail
    dm.init(engine=engine)
    assert caplog.records[0].message == "Session already initialized.  Bailing"


def test_init_no_init_twice(datanommer_models, mocker, caplog):
    dm.init("sqlite:///db.db")
    assert caplog.records[0].message == "Session already initialized.  Bailing"


def test_unclassified_category(datanommer_models):
    example_message = generate_message(topic="too.short")
    dm.add(example_message)
    dbmsg = dm.session.scalar(select(dm.Message))

    assert dbmsg.category == "Unclassified"


def test_from_msg_id(datanommer_models):
    example_message = generate_message()
    example_message.id = "ACUSTOMMESSAGEID"
    dm.add(example_message)
    dbmsg = dm.Message.from_msg_id("ACUSTOMMESSAGEID")

    assert dbmsg.msg_id == "ACUSTOMMESSAGEID"


def test_add_missing_msg_id(datanommer_models, caplog):
    caplog.set_level(logging.INFO)
    example_message = generate_message()
    example_message._properties.message_id = None
    dm.add(example_message)
    dbmsg = dm.session.scalar(select(dm.Message))
    assert (
        "Message on org.fedoraproject.test.a.nice.message was received without a msg_id"
        in caplog.records[-1].message
    )
    assert dbmsg.msg_id is not None


def test_add_missing_timestamp(datanommer_models):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = None

    dm.add(example_message)

    dbmsg = dm.session.scalar(select(dm.Message))
    timediff = datetime.datetime.now() - dbmsg.timestamp
    # 60 seconds between adding the message and checking
    # the timestamp should be more than enough.
    assert timediff < datetime.timedelta(seconds=60)


def test_add_timestamp_with_Z(datanommer_models):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = "2021-07-27T04:22:42Z"

    dm.add(example_message)

    dbmsg = dm.session.scalar(select(dm.Message))
    assert dbmsg.timestamp.astimezone(datetime.timezone.utc) == datetime.datetime(
        2021, 7, 27, 4, 22, 42, tzinfo=datetime.timezone.utc
    )


def test_add_timestamp_with_junk(datanommer_models, caplog):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = "2021-07-27T04:22:42JUNK"

    dm.add(example_message)

    assert "Failed to parse sent-at timestamp value" in caplog.records[0].message

    assert dm.session.scalar(select(func.count(dm.Message.id))) == 0


def test_add_and_check_for_others(datanommer_models):
    # There are no users or packages at the start
    assert dm.session.scalar(select(func.count(dm.User.id))) == 0
    assert dm.session.scalar(select(func.count(dm.Package.id))) == 0

    # Then add a message
    dm.add(generate_bodhi_update_complete_message())

    # There should now be two of each
    assert dm.session.scalar(select(func.count(dm.User.id))) == 2
    assert dm.session.scalar(select(func.count(dm.Package.id))) == 2

    # If we add it again, there should be no duplicates
    dm.add(generate_bodhi_update_complete_message())
    assert dm.session.scalar(select(func.count(dm.User.id))) == 2
    assert dm.session.scalar(select(func.count(dm.Package.id))) == 2

    # Add a new username
    dm.add(generate_bodhi_update_complete_message(text="this is @abompard in a comment"))
    assert dm.session.scalar(select(func.count(dm.User.id))) == 3
    assert dm.session.scalar(select(func.count(dm.Package.id))) == 2


def test_add_nothing(datanommer_models):
    assert dm.session.scalar(select(func.count(dm.Message.id))) == 0


def test_add_and_check(datanommer_models):
    dm.add(generate_message())
    dm.session.flush()
    assert dm.session.scalar(select(func.count(dm.Message.id))) == 1


def test_categories(datanommer_models):
    dm.add(generate_bodhi_update_complete_message())
    dm.session.flush()
    obj = dm.session.scalar(select(dm.Message))
    assert obj.category == "bodhi"


def test_categories_with_umb(datanommer_models):
    dm.add(generate_message(topic="/topic/VirtualTopic.eng.brew.task.closed"))
    dm.session.flush()
    obj = dm.session.scalar(select(dm.Message))
    assert obj.category == "brew"


def test_grep_all(datanommer_models):
    example_message = generate_message()
    print("example message:", repr(example_message))
    print(repr(example_message.body))
    dm.add(example_message)
    dm.session.flush()
    t, p, r = dm.Message.grep()
    assert t == 1
    assert p == 1
    assert len(r) == 1
    print(repr(r))
    assert r[0].msg == example_message.body


def test_grep_category(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    dm.add(example_message)
    dm.session.flush()
    t, p, r = dm.Message.grep(categories=["bodhi"])
    assert t == 1
    assert p == 1
    assert len(r) == 1
    assert r[0].msg == example_message.body


def test_grep_not_category(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    dm.add(example_message)
    dm.session.flush()
    t, p, r = dm.Message.grep(not_categories=["bodhi"])
    assert t == 0
    assert p == 0
    assert len(r) == 0


def test_add_headers(datanommer_models):
    example_headers = {"foo": "bar", "baz": 1, "wibble": ["zork", "zap"]}
    example_message = generate_message(
        topic="org.fedoraproject.prod.bodhi.newupdate", headers=example_headers
    )
    dm.add(example_message)
    dbmsg = dm.session.scalar(select(dm.Message))
    assert dbmsg.headers["foo"] == "bar"
    assert dbmsg.headers["baz"] == 1
    assert dbmsg.headers["wibble"] == ["zork", "zap"]


def test_grep_topics(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    dm.add(example_message)
    dm.session.flush()
    t, p, r = dm.Message.grep(topics=["org.fedoraproject.prod.bodhi.newupdate"])
    assert t == 1
    assert p == 1
    assert len(r) == 1
    assert r[0].msg == example_message.body


def test_grep_not_topics(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    dm.add(example_message)
    dm.session.flush()
    t, p, r = dm.Message.grep(not_topics=["org.fedoraproject.prod.bodhi.newupdate"])
    assert t == 0
    assert p == 0
    assert len(r) == 0


def test_grep_start_end_validation(datanommer_models):
    with pytest.raises(
        ValueError,
        match="Either both start and end must be specified or neither must be specified",
    ):
        dm.Message.grep(start="2020-03-26")
    with pytest.raises(
        ValueError,
        match="Either both start and end must be specified or neither must be specified",
    ):
        dm.Message.grep(end="2020-03-26")


def test_grep_start_end(datanommer_models):
    example_message = generate_message()
    example_message._properties.headers["sent-at"] = "2021-04-01T00:00:01"
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    bodhi_example_message._properties.headers["sent-at"] = "2021-06-01T00:00:01"
    dm.add(bodhi_example_message)

    dm.session.flush()
    total, pages, messages = dm.Message.grep(start="2021-04-01", end="2021-05-01")
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == example_message.body

    total, pages, messages = dm.Message.grep(start="2021-06-01", end="2021-07-01")
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == bodhi_example_message.body


def test_grep_msg_id(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    dm.add(bodhi_example_message)

    dm.session.flush()
    total, pages, messages = dm.Message.grep(msg_id=example_message.id)
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == example_message.body

    total, pages, messages = dm.Message.grep(msg_id=bodhi_example_message.id)
    assert total == 1
    assert pages == 1
    assert len(messages) == 1
    assert messages[0].msg == bodhi_example_message.body

    total, pages, messages = dm.Message.grep(msg_id="NOTAMESSAGEID")
    assert total == 0
    assert pages == 0
    assert len(messages) == 0


def test_grep_agents(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    dm.add(bodhi_example_message)

    dm.session.flush()

    total, pages, messages = dm.Message.grep(agents=["dudemcpants"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == bodhi_example_message.body


def test_grep_not_agents(datanommer_models, mocker):
    example_message = generate_message()  # has agent_name == None
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    dm.add(bodhi_example_message)  # has agent_name == "dudemcpants"

    class MessageWithAgent(fedora_message.Message):
        topic = "org.fedoraproject.test.a.message.with.agent"
        agent_name = "dummy-agent-name"

    fedora_message._schema_name_to_class["MessageWithAgent"] = MessageWithAgent
    fedora_message._class_to_schema_name[MessageWithAgent] = "MessageWithAgent"

    example_message_with_agent = MessageWithAgent(
        body={"subject": "this is a message with an agent"}
    )
    dm.add(example_message_with_agent)

    dm.session.flush()

    total, pages, messages = dm.Message.grep(not_agents=["dudemcpants"])

    # Messages with agent_name == None are not returned
    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == example_message_with_agent.body


def test_grep_users(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    dm.add(bodhi_example_message)

    dm.session.flush()

    total, pages, messages = dm.Message.grep(users=["dudemcpants"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == bodhi_example_message.body


def test_grep_not_users(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    dm.add(bodhi_example_message)

    dm.session.flush()

    total, pages, messages = dm.Message.grep(not_users=["dudemcpants"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == example_message.body


def test_grep_packages(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    dm.add(bodhi_example_message)

    dm.session.flush()

    total, pages, messages = dm.Message.grep(packages=["kernel"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == bodhi_example_message.body


def test_grep_not_packages(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    bodhi_example_message = generate_bodhi_update_complete_message()
    dm.add(bodhi_example_message)

    dm.session.flush()

    total, pages, messages = dm.Message.grep(not_packages=["kernel"])

    assert total == 1
    assert pages == 1
    assert len(messages) == 1

    assert messages[0].msg == example_message.body


def test_grep_contains(datanommer_models):
    example_message = generate_message(topic="org.fedoraproject.prod.bodhi.newupdate")
    dm.add(example_message)
    dm.session.flush()
    t, p, r = dm.Message.grep(contains=["doing"])
    assert t == 1
    assert p == 1
    assert len(r) == 1
    assert r[0].msg == example_message.body


def test_grep_rows_per_page(datanommer_models, add_200_messages):
    total, pages, messages = dm.Message.grep()
    assert total == 200
    assert pages == 2
    assert len(messages) == 100

    for rows_per_page in (None, 0):
        try:
            total, pages, messages = dm.Message.grep(rows_per_page=rows_per_page)
        except ZeroDivisionError as e:
            pytest.fail(e)
        assert total == 200
        assert pages == 1
        assert len(messages) == 200


def test_grep_defer(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    dm.session.flush()

    total, pages, query = dm.Message.grep(defer=True)
    assert isinstance(query, Select)

    assert dm.session.scalars(query).all() == dm.Message.grep()[2]


def test_grep_no_paging_and_defer(datanommer_models, add_200_messages):
    total, pages, messages = dm.Message.grep(rows_per_page=0, defer=True)
    assert total == 200
    assert pages == 1


def test_grep_no_total_if_single_page(datanommer_models, add_200_messages, mocker):
    # Assert we don't query the total of messages if we're getting them all anyway
    scalar_spy = mocker.spy(dm.session, "scalar")
    total, pages, messages = dm.Message.grep(rows_per_page=0)
    assert total == 200
    scalar_spy.assert_not_called()


def test_get_first(datanommer_models):
    messages = []
    for x in range(0, 200):
        example_message = generate_message()
        example_message.id = f"{x}"
        dm.add(example_message)
        messages.append(example_message)
    dm.session.flush()
    msg = dm.Message.get_first()
    assert msg.msg_id == "0"
    assert msg.msg == messages[0].body


def test_add_duplicate(datanommer_models, caplog):
    example_message = generate_message()
    dm.add(example_message)
    dm.add(example_message)
    # if no exception was thrown, then we successfully ignored the
    # duplicate message
    assert dm.session.scalar(select(func.count(dm.Message.id))) == 1
    assert (
        "Skipping message from org.fedoraproject.test.a.nice.message" in caplog.records[0].message
    )


def test_add_integrity_error(datanommer_models, mocker, caplog):
    mock_session_add = mocker.patch("datanommer.models.session.add")
    mock_session_add.side_effect = IntegrityError("asdf", "asd", "asdas")
    example_message = generate_message()
    dm.add(example_message)
    assert "Unknown Integrity Error: message" in caplog.records[0].message
    assert dm.session.scalar(select(func.count(dm.Message.id))) == 0


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
        dm.add(example_message)
    except IntegrityError as e:
        pytest.fail(e)
    assert dm.session.scalar(select(func.count(dm.Message.id))) == 1
    dbmsg = dm.session.scalar(select(dm.Message))
    assert len(dbmsg.packages) == 1
    assert dbmsg.packages[0].name == "pkg"


@pytest.mark.parametrize(
    "property_name,name_in_msg", [("usernames", "users"), ("packages", "packages")]
)
def test_add_message_with_error_on_property(datanommer_models, caplog, property_name, name_in_msg):
    # Define a special message schema and register it
    class CustomMessage(fedora_message.Message):
        @property
        def packages(self):
            raise KeyError

        def _filter_headers(self):
            return {}

    def _crash(self):
        raise KeyError

    setattr(CustomMessage, property_name, property(_crash))

    fedora_message._schema_name_to_class["CustomMessage"] = CustomMessage
    fedora_message._class_to_schema_name[CustomMessage] = "CustomMessage"
    example_message = CustomMessage(
        topic="org.fedoraproject.test.a.nice.message",
        body={"encouragement": "You're doing great!"},
        headers=None,
    )
    try:
        dm.add(example_message)
    except KeyError as e:
        pytest.fail(e)
    assert dm.session.scalar(select(func.count(dm.Message.id))) == 1
    assert caplog.records[0].message == (
        f"Could not get the list of {name_in_msg} from a message on "
        f"org.fedoraproject.test.a.nice.message with id {example_message.id}"
    )


def test_as_fedora_message_dict(datanommer_models):
    example_message = generate_message()
    dm.add(example_message)

    dbmsg = dm.session.scalar(select(dm.Message))

    message_json = json.dumps(dbmsg.as_fedora_message_dict())

    # this should be the same as if we use the fedora_messaging dump function
    assert json.loads(fedora_message.dumps(example_message)) == json.loads(message_json)


def test_as_fedora_message_dict_old_headers(datanommer_models):
    # Messages received with fedmsg don't have the sent-at header
    example_message = generate_message()
    dm.add(example_message)

    dbmsg = dm.session.scalar(select(dm.Message))
    del dbmsg.headers["sent-at"]

    message_dict = dbmsg.as_fedora_message_dict()
    print(message_dict)
    print(json.loads(fedora_message.dumps(example_message)))

    # this should be the same as if we use the fedora_messaging dump function
    assert json.loads(fedora_message.dumps(example_message)) == message_dict


def test_as_fedora_message_dict_no_headers(datanommer_models):
    # Messages can have no headers
    example_message = generate_message()
    dm.add(example_message)

    dbmsg = dm.session.scalar(select(dm.Message))
    assert len(dbmsg.headers.keys()) == 5

    # Clear the headers
    dbmsg.headers = None

    try:
        message_dict = dbmsg.as_fedora_message_dict()
    except TypeError as e:
        pytest.fail(e)

    assert list(message_dict["headers"].keys()) == ["sent-at"]


def test_as_dict(datanommer_models):
    dm.add(generate_message())
    dbmsg = dm.session.scalar(select(dm.Message))
    message_dict = dbmsg.as_dict()

    # we should have 14 keys in this dict
    assert len(message_dict) == 15
    assert message_dict["msg"] == {"encouragement": "You're doing great!"}
    assert message_dict["topic"] == "org.fedoraproject.test.a.nice.message"


def test_as_dict_with_users_and_packages(datanommer_models):
    dm.add(generate_bodhi_update_complete_message())
    dbmsg = dm.session.scalar(select(dm.Message))
    message_dict = dbmsg.as_dict()

    assert message_dict["users"] == ["dudemcpants", "ryanlerch"]
    assert message_dict["packages"] == ["abrt-addon-python3", "kernel"]


def test___json__deprecated(datanommer_models, caplog, mocker):
    mock_as_dict = mocker.patch("datanommer.models.Message.as_dict")

    dm.add(generate_message())

    with pytest.warns(DeprecationWarning):
        dbmsg = dm.session.scalar(select(dm.Message))
        dbmsg.__json__()

    mock_as_dict.assert_called_once()


def test_username_deprecated(datanommer_models, caplog, mocker):
    dm.add(generate_message())
    dbmsg = dm.session.scalar(select(dm.Message))
    dbmsg.agent_name = "dummy"

    with pytest.warns(DeprecationWarning):
        assert dbmsg.username == "dummy"


def test_singleton_create(datanommer_models):
    dm.Package.get_or_create("foobar")
    assert [p.name for p in dm.session.scalars(select(dm.Package))] == ["foobar"]


def test_singleton_get_existing(datanommer_models):
    p1 = dm.Package.get_or_create("foobar")
    # Clear the in-memory cache
    dm.Package._cache.clear()
    p2 = dm.Package.get_or_create("foobar")
    assert p1.id == p2.id
