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
import json
import time
from datetime import datetime, timedelta

import pytest

import datanommer.commands
import datanommer.models as m


@pytest.fixture
def mocked_config(fedmsg_config, mocker):
    fedmsg_config["logging"] = {"version": 1}
    for cmd_class in ("StatsCommand", "DumpCommand", "LatestCommand"):
        gc = mocker.patch(f"datanommer.commands.{cmd_class}.get_config")
        gc.return_value = fedmsg_config
    return fedmsg_config


def test_stats(datanommer_models, mocked_config):
    mocked_config["topic"] = False

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create",
        category="fas",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.StatsCommand()

    command.log.info = info
    command.run()

    assert "git has 2 entries" in logged_info
    assert "fas has 1 entries" in logged_info


def test_stats_topics(datanommer_models, mocked_config):
    mocked_config["topic"] = True

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create",
        category="fas",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.StatsCommand()

    command.log.info = info
    command.run()

    assert (
        "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries"
        in logged_info
    )
    assert "org.fedoraproject.stg.fas.user.create has 1 entries" in logged_info
    assert (
        "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries" in logged_info
    )


def test_stats_cat_topics(datanommer_models, mocked_config):
    mocked_config["topic"] = True
    mocked_config["category"] = "git"

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create",
        category="fas",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.StatsCommand()

    command.log.info = info
    command.run()

    assert (
        "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries"
        in logged_info
    )
    assert "org.fedoraproject.stg.fas.user.create has 1 entries" not in logged_info
    assert (
        "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries" in logged_info
    )


def test_dump(datanommer_models, mocked_config, mocker):
    m.Message = datanommer.models.Message
    now = datetime.utcnow()

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master", timestamp=now
    )

    msg2 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master", timestamp=now
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    objects = [msg1, msg2]

    # models = [m.Message]

    # mocker.patch("datanommer.models.models", models)
    mocker.patch("datanommer.models.Message.query")

    m.Message.query.all = mocker.Mock(return_value=objects)

    command = datanommer.commands.DumpCommand()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command.log.info = info
    command.run()

    json_object = json.loads(logged_info[0])

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.branch.valgrind.master"
    )


def test_dump_before(datanommer_models, mocker, mocked_config):
    m.Message = datanommer.models.Message

    mocked_config["before"] = "2013-02-16"

    time1 = datetime(2013, 2, 14)
    time2 = datetime(2013, 2, 15)
    time3 = datetime(2013, 2, 16, 8)

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=time1,
        i=4,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=time2,
        i=3,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.log.receive.valgrind.master",
        timestamp=time3,
        i=2,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.DumpCommand()

    command.log.info = info
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = datetime(2013, 3, 1)
    mock_dt.now.return_value = datetime(2013, 3, 1)
    command.run()

    json_object = json.loads(logged_info[0])

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.branch.valgrind.master"
    )
    assert (
        json_object[1]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    )
    assert len(json_object) == 2


def test_dump_since(datanommer_models, mocker, mocked_config):
    mocked_config["since"] = "2013-02-14T08:00:00"

    time1 = datetime(2013, 2, 14)
    time2 = datetime(2013, 2, 15)
    time3 = datetime(2013, 2, 16, 8)

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=time1,
        i=4,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=time2,
        i=3,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.log.receive.valgrind.master",
        timestamp=time3,
        i=2,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.DumpCommand()

    command.log.info = info
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = datetime(2013, 3, 1)
    mock_dt.now.return_value = datetime(2013, 3, 1)
    command.run()

    json_object = json.loads(logged_info[0])

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    )
    assert (
        json_object[1]["topic"] == "org.fedoraproject.prod.log.receive.valgrind.master"
    )
    assert len(json_object) == 2


def test_dump_timespan(datanommer_models, mocker, mocked_config):

    mocked_config["before"] = "2013-02-16"
    mocked_config["since"] = "2013-02-14T08:00:00"

    time1 = datetime(2013, 2, 14)
    time2 = datetime(2013, 2, 15)
    time3 = datetime(2013, 2, 16, 8)

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=time1,
        i=4,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=time2,
        i=3,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.log.receive.valgrind.master",
        timestamp=time3,
        i=2,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.DumpCommand()

    command.log.info = info
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = datetime(2013, 3, 1)
    mock_dt.now.return_value = datetime(2013, 3, 1)
    command.run()

    json_object = json.loads(logged_info[0])

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    )
    assert len(json_object) == 1


def test_latest_overall(datanommer_models, mocked_config):
    mocked_config["overall"] = True

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    command.run()

    json_object = json.loads(logged_info[0])

    assert json_object[0]["git"]["msg"] == "Message 3"
    assert len(json_object) == 1


def test_latest_topic(datanommer_models, mocked_config):
    mocked_config["topic"] = "org.fedoraproject.stg.fas.user.create"

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    command.run()

    json_object = json.loads(logged_info[0])

    assert json_object[0]["fas"]["msg"] == "Message 2"
    assert len(json_object) == 1


def test_latest_category(datanommer_models, mocked_config):
    mocked_config["category"] = "fas"

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create",
        category="fas",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        category="git",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    command.run()

    json_object = json.loads(logged_info[0])

    assert json_object[0]["fas"]["msg"] == "Message 2"
    assert len(json_object) == 1


def test_latest_timestamp_human(datanommer_models, mocker, mocked_config):
    mocked_config["overall"] = False
    mocked_config["timestamp"] = True
    mocked_config["human"] = True

    time1 = datetime(2013, 2, 14)
    time2 = datetime(2013, 2, 15, 15, 15, 15, 15)
    time3 = datetime(2013, 2, 16, 16, 16, 16, 16)

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=time1,
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=time3,
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = datetime(2013, 3, 1)
    mock_dt.now.return_value = datetime(2013, 3, 1)
    command.run()

    json_object = json.loads(logged_info[0])

    assert json_object[1] == "2013-02-16 16:16:16.000016"
    assert json_object[0] == "2013-02-15 15:15:15.000015"
    assert len(json_object) == 2


def test_latest_timestamp(datanommer_models, mocker, mocked_config):
    mocked_config["overall"] = False
    mocked_config["timestamp"] = True

    time1 = datetime(2013, 2, 14)
    time2 = datetime(2013, 2, 15)
    time3 = datetime(2013, 2, 16)

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=time1,
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=time3,
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = datetime(2013, 3, 1)
    mock_dt.now.return_value = datetime(2013, 3, 1)
    command.run()

    json_object = json.loads(logged_info[0])

    assert json_object[1] == time.mktime(datetime(2013, 2, 16).timetuple())
    assert json_object[0] == time.mktime(datetime(2013, 2, 15).timetuple())
    assert len(json_object) == 2


def test_latest_timesince(datanommer_models, mocker, mocked_config):
    mocked_config["overall"] = False
    mocked_config["timesince"] = True

    now = datetime(2013, 3, 1)
    time1 = now - timedelta(days=1)
    time2 = now - timedelta(seconds=60)
    time3 = now - timedelta(seconds=1)

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=time1,
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=time3,
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = now
    mock_dt.now.return_value = now
    command.run()

    json_object = json.loads(logged_info[0])

    # allow .1 second to run test
    assert int(json_object[1]) <= 1.1
    assert int(json_object[1]) >= 1
    assert int(json_object[0]) <= 60.1
    assert int(json_object[0]) >= 60
    assert len(json_object) == 2


def test_latest_timesince_human(datanommer_models, mocked_config):
    mocked_config["overall"] = False
    mocked_config["timesince"] = True
    mocked_config["human"] = True

    now = datetime.now()
    time1 = now - timedelta(days=2)
    time2 = now - timedelta(days=1)
    time3 = now - timedelta(seconds=1)

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=time1,
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=time3,
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    command.run()

    json_object = json.loads(logged_info[0])

    # cannot assert exact value because of time to run test
    assert "day" not in json_object[1]
    assert "0:00:01." in json_object[1]
    assert "1 day in 0:00:00.", json_object[0]
    assert len(json_object) == 2


def test_latest(datanommer_models, mocked_config):
    mocked_config["overall"] = False

    msg1 = m.Message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg2 = m.Message(
        topic="org.fedoraproject.stg.fas.user.create",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg3 = m.Message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        timestamp=datetime.utcnow(),
        i=1,
    )

    msg1.msg = "Message 1"
    msg2.msg = "Message 2"
    msg3.msg = "Message 3"

    m.session.add_all([msg1, msg2, msg3])
    m.session.flush()

    logged_info = []

    def info(data):
        logged_info.append(data)

    command = datanommer.commands.LatestCommand()

    command.log.info = info
    command.run()

    json_object = json.loads(logged_info[0])

    assert json_object[1]["git"]["msg"] == "Message 3"
    assert json_object[0]["fas"]["msg"] == "Message 2"
    assert len(json_object) == 2
