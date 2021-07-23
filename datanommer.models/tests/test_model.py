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

from fedora_messaging import message as fedora_message

from datanommer.models import add, Message, session


def generate_message(
    topic="nice.message", body={"encouragement": "You're doing great!"}, headers=None
):
    return fedora_message.Message(topic=topic, body=body, headers=headers)


def test_add_nothing(datanommer_models):
    assert Message.query.count() == 0


def test_add_and_check(datanommer_models):
    add(generate_message())
    session.flush()
    assert Message.query.count() == 1


def test_categories(datanommer_models):
    add(generate_message(topic="org.fedoraproject.prod.bodhi.newupdate"))
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


def test_add_duplicate(datanommer_models):
    example_message = generate_message()
    add(example_message)
    add(example_message)
    # if no exception was thrown, then we successfully ignored the
    # duplicate message
    assert Message.query.count() == 1
