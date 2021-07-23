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
from click.testing import CliRunner

import datanommer.commands
import datanommer.models as m


@pytest.fixture
def get_url(mocker):
    mock_get_url = mocker.patch("datanommer.commands.get_datanommer_sqlalchemy_url")
    mock_get_url.return_value = "sqlite:///fake.db"


def test_stats(datanommer_models, get_url):
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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.stats, [])

    assert "git has 2 entries" in result.output
    assert "fas has 1 entries" in result.output


def test_stats_topics(datanommer_models, get_url):

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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.stats, ["--topic"])

    assert (
        "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries"
        in result.output
    )
    assert "org.fedoraproject.stg.fas.user.create has 1 entries" in result.output
    assert (
        "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries"
        in result.output
    )


def test_stats_cat_topics(datanommer_models, get_url):
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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.stats, ["--topic", "--category", "git"])

    assert (
        "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries"
        in result.output
    )
    assert "org.fedoraproject.stg.fas.user.create has 1 entries" not in result.output
    assert (
        "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries"
        in result.output
    )


def test_dump(datanommer_models, mocker, get_url):
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

    mocker.patch("datanommer.models.Message.query")

    m.Message.query.all = mocker.Mock(return_value=objects)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, [])

    json_object = json.loads(result.output)

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.branch.valgrind.master"
    )


def test_dump_before(datanommer_models, mocker, get_url):
    m.Message = datanommer.models.Message

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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, ["--before", "2013-02-16"])

    json_object = json.loads(result.output)

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.branch.valgrind.master"
    )
    assert (
        json_object[1]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    )
    assert len(json_object) == 2


def test_dump_since(datanommer_models, mocker, get_url):
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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, ["--since", "2013-02-14T08:00:00"])

    json_object = json.loads(result.output)

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    )
    assert (
        json_object[1]["topic"] == "org.fedoraproject.prod.log.receive.valgrind.master"
    )
    assert len(json_object) == 2


def test_dump_timespan(datanommer_models, mocker, get_url):

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

    runner = CliRunner()
    result = runner.invoke(
        datanommer.commands.dump,
        ["--before", "2013-02-16", "--since", "2013-02-14T08:00:00"],
    )

    json_object = json.loads(result.output)

    assert (
        json_object[0]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    )
    assert len(json_object) == 1


def test_dump_invalid_dates(datanommer_models, mocker, get_url):
    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, ["--before", "2013-02-16asdasd"])
    assert result.output == "Error: Invalid date format\n"

    result = runner.invoke(datanommer.commands.dump, ["--since", "2013-02-16asdasd"])
    assert result.output == "Error: Invalid date format\n"


def test_latest_overall(datanommer_models, get_url):

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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--overall"])

    json_object = json.loads(result.output)

    assert json_object[0]["git"] == "Message 3"
    assert len(json_object) == 1


def test_latest_topic(datanommer_models, get_url):

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

    runner = CliRunner()
    result = runner.invoke(
        datanommer.commands.latest, ["--topic", "org.fedoraproject.stg.fas.user.create"]
    )

    json_object = json.loads(result.output)

    assert json_object[0]["fas"] == "Message 2"
    assert len(json_object) == 1


def test_latest_category(datanommer_models, get_url):
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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--category", "fas"])

    json_object = json.loads(result.output)

    assert json_object[0]["fas"] == "Message 2"
    assert len(json_object) == 1


def test_latest_timestamp_human(datanommer_models, mocker, get_url):
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

    # datanommer-latest defaults to the last year, so mock the
    # datetime calls to go back to 2013
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = datetime(2013, 3, 1)
    mock_dt.now.return_value = datetime(2013, 3, 1)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timestamp", "--human"])

    json_object = json.loads(result.output)

    assert json_object[1] == "2013-02-16 16:16:16.000016"
    assert json_object[0] == "2013-02-15 15:15:15.000015"
    assert len(json_object) == 2


def test_latest_timestamp(datanommer_models, mocker, get_url):

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

    # datanommer-latest defaults to the last year, so mock the
    # datetime calls to go back to 2013
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = datetime(2013, 3, 1)
    mock_dt.now.return_value = datetime(2013, 3, 1)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timestamp"])

    json_object = json.loads(result.output)

    assert json_object[1] == time.mktime(datetime(2013, 2, 16).timetuple())
    assert json_object[0] == time.mktime(datetime(2013, 2, 15).timetuple())
    assert len(json_object) == 2


def test_latest_timesince(datanommer_models, mocker, get_url):

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

    # datanommer-latest defaults to the last year, so mock the
    # datetime calls to go back to 2013
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.utcnow.return_value = now
    mock_dt.now.return_value = now

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timesince"])

    json_object = json.loads(result.output)

    # allow .1 second to run test
    assert int(json_object[1]) <= 1.1
    assert int(json_object[1]) >= 1
    assert int(json_object[0]) <= 60.1
    assert int(json_object[0]) >= 60
    assert len(json_object) == 2


def test_latest_timesince_human(datanommer_models, get_url):

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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timesince", "--human"])

    json_object = json.loads(result.output)

    # cannot assert exact value because of time to run test
    assert "day" not in json_object[1]
    assert "0:00:01." in json_object[1]
    assert "1 day in 0:00:00.", json_object[0]
    assert len(json_object) == 2


def test_latest(datanommer_models, get_url):
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

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, [])

    json_object = json.loads(result.output)

    assert json_object[1]["git"] == "Message 3"
    assert json_object[0]["fas"] == "Message 2"
    assert len(json_object) == 2
