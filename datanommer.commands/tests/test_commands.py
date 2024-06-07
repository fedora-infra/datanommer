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
from click import ClickException
from click.testing import CliRunner

import datanommer.commands
import datanommer.models as m

from .utils import generate_bodhi_update_complete_message, generate_message


def test_get_datanommer_sqlalchemy_url_keyerror(mocker):
    mocker.patch.dict(
        datanommer.commands.utils.fedora_messaging_config.conf["consumer_config"],
        {},
        clear=True,
    )
    with pytest.raises(ClickException):
        datanommer.commands.get_config()


def test_get_datanommer_sqlalchemy_url_config(mocker):
    conf = {
        "datanommer_sqlalchemy_url": "",
        "alembic_ini": "/some/where",
    }
    mocker.patch.dict(
        datanommer.commands.utils.fedora_messaging_config.conf["consumer_config"], conf
    )
    load_config = mocker.patch(
        "datanommer.commands.utils.fedora_messaging_config.conf.load_config",
    )
    datanommer.commands.get_config("some-path")
    load_config.assert_called_with("some-path")


def test_create(mocker):
    mock_model_init = mocker.patch("datanommer.commands.m.init")
    mocker.patch.dict(
        datanommer.commands.utils.fedora_messaging_config.conf["consumer_config"],
        {
            "datanommer_sqlalchemy_url": "TESTURL",
            "alembic_ini": "/some/where",
        },
    )

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.create, [])
    assert result.exit_code == 0, result.output

    assert result.output == "Creating Datanommer database and tables\n"
    mock_model_init.assert_called_once_with("TESTURL", alembic_ini="/some/where", create=True)


def test_stats(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.stats, [])
    assert result.exit_code == 0, result.output

    assert "git has 2 entries" in result.output
    assert "fas has 1 entries" in result.output


def test_stats_topics(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.stats, ["--topic"])
    assert result.exit_code == 0, result.output

    assert "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries" in result.output
    assert "org.fedoraproject.stg.fas.user.create has 1 entries" in result.output
    assert "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries" in result.output


def test_stats_category_topics(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.stats, ["--topic", "--category", "git"])
    assert result.exit_code == 0, result.output

    assert "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries" in result.output
    assert "org.fedoraproject.stg.fas.user.create has 1 entries" not in result.output
    assert "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries" in result.output


def test_stats_category(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.stats, ["--category", "git"])
    assert result.exit_code == 0, result.output

    assert result.output == "git has 2 entries\n"


def test_dump(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    m.add(msg2)

    msg3 = generate_bodhi_update_complete_message()
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, [])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[0]["topic"] == "org.fedoraproject.prod.git.branch.valgrind.master"


def test_dump_before(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    msg1._properties.headers["sent-at"] = datetime(2013, 2, 14).isoformat()
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.prod.git.receive.valgrind.master")
    msg2._properties.headers["sent-at"] = datetime(2013, 2, 15).isoformat()
    m.add(msg2)

    msg3 = generate_message(topic="org.fedoraproject.prod.log.receive.valgrind.master")
    msg3._properties.headers["sent-at"] = datetime(2013, 2, 16, 8).isoformat()
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, ["--before", "2013-02-16"])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[0]["topic"] == "org.fedoraproject.prod.git.branch.valgrind.master"
    assert json_object[1]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    assert len(json_object) == 2


def test_dump_since(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    msg1._properties.headers["sent-at"] = datetime(2013, 2, 14).isoformat()
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.prod.git.receive.valgrind.master")
    msg2._properties.headers["sent-at"] = datetime(2013, 2, 15).isoformat()
    m.add(msg2)

    msg3 = generate_message(topic="org.fedoraproject.prod.log.receive.valgrind.master")
    msg3._properties.headers["sent-at"] = datetime(2013, 2, 16, 8).isoformat()
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, ["--since", "2013-02-14T08:00:00"])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[0]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    assert json_object[1]["topic"] == "org.fedoraproject.prod.log.receive.valgrind.master"
    assert len(json_object) == 2


def test_dump_timespan(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    msg1._properties.headers["sent-at"] = datetime(2013, 2, 14).isoformat()
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.prod.git.receive.valgrind.master")
    msg2._properties.headers["sent-at"] = datetime(2013, 2, 15).isoformat()
    m.add(msg2)

    msg3 = generate_message(topic="org.fedoraproject.prod.log.receive.valgrind.master")
    msg3._properties.headers["sent-at"] = datetime(2013, 2, 16, 8).isoformat()
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(
        datanommer.commands.dump,
        ["--before", "2013-02-16", "--since", "2013-02-14T08:00:00"],
    )
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[0]["topic"] == "org.fedoraproject.prod.git.receive.valgrind.master"
    assert len(json_object) == 1


def test_dump_invalid_dates(datanommer_models, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(datanommer.commands.dump, ["--before", "2013-02-16asdasd"])
    assert result.exit_code > 0, result.output
    assert result.output == "Error: Invalid date format\n"

    result = runner.invoke(datanommer.commands.dump, ["--since", "2013-02-16asdasd"])
    assert result.exit_code > 0, result.output
    assert result.output == "Error: Invalid date format\n"


def test_latest_overall(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--overall"])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[0]["git"]["body"] == {"Message 3": "Message 3"}
    assert len(json_object) == 1


def test_latest_topic(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(
        datanommer.commands.latest, ["--topic", "org.fedoraproject.stg.fas.user.create"]
    )
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[0]["fas"]["body"] == {"Message 2": "Message 2"}
    assert len(json_object) == 1


def test_latest_category(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--category", "fas"])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[0]["fas"]["body"] == {"Message 2": "Message 2"}
    assert len(json_object) == 1


def test_latest_timestamp_human(datanommer_models, mocker, mock_config, mock_init):
    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    msg1._properties.headers["sent-at"] = datetime(2013, 2, 14).isoformat()
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.stg.fas.user.create")
    msg2._properties.headers["sent-at"] = datetime(2013, 2, 15, 15, 15, 15, 15).isoformat()
    m.add(msg2)

    msg3 = generate_message(topic="org.fedoraproject.prod.git.receive.valgrind.master")
    msg3._properties.headers["sent-at"] = datetime(2013, 2, 16, 16, 16, 16, 16).isoformat()
    m.add(msg3)

    # datanommer-latest defaults to the last year, so mock the
    # datetime calls to go back to 2013
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.now.return_value = datetime(2013, 3, 1)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timestamp", "--human"])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[1] == "2013-02-16 16:16:16.000016"
    assert json_object[0] == "2013-02-15 15:15:15.000015"
    assert len(json_object) == 2


def test_latest_timestamp(datanommer_models, mocker, mock_config, mock_init):
    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    msg1._properties.headers["sent-at"] = datetime(2013, 2, 14).isoformat()
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.stg.fas.user.create")
    msg2._properties.headers["sent-at"] = datetime(2013, 2, 15).isoformat()
    m.add(msg2)

    msg3 = generate_message(topic="org.fedoraproject.prod.git.receive.valgrind.master")
    msg3._properties.headers["sent-at"] = datetime(2013, 2, 16).isoformat()
    m.add(msg3)

    # datanommer-latest defaults to the last year, so mock the
    # datetime calls to go back to 2013
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.now.return_value = datetime(2013, 3, 1)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timestamp"])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[1] == time.mktime(datetime(2013, 2, 16).timetuple())
    assert json_object[0] == time.mktime(datetime(2013, 2, 15).timetuple())
    assert len(json_object) == 2


def test_latest_timesince(datanommer_models, mocker, mock_config, mock_init):
    now = datetime(2013, 3, 1)

    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    time1 = now - timedelta(days=1)
    msg1._properties.headers["sent-at"] = time1.isoformat()
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.stg.fas.user.create")
    time2 = now - timedelta(seconds=60)
    msg2._properties.headers["sent-at"] = time2.isoformat()
    m.add(msg2)

    msg3 = generate_message(topic="org.fedoraproject.prod.git.receive.valgrind.master")
    time3 = now - timedelta(seconds=1)
    msg3._properties.headers["sent-at"] = time3.isoformat()
    m.add(msg3)

    # datanommer-latest defaults to the last year, so mock the
    # datetime calls to go back to 2013
    mock_dt = mocker.patch("datanommer.commands.datetime")
    mock_dt.now.return_value = now

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timesince"])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    # allow .1 second to run test
    assert int(json_object[1]) <= 1.1
    assert int(json_object[1]) >= 1
    assert int(json_object[0]) <= 60.1
    assert int(json_object[0]) >= 60
    assert len(json_object) == 2


def test_latest_timesince_human(datanommer_models, mock_config, mock_init, mocker):
    now = datetime.now()
    # mocker.patch.object(datanommer.commands.datetime, "now", return_value=now)
    patched_datetime = mocker.patch("datanommer.commands.datetime", mocker.Mock(wraps=datetime))
    patched_datetime.now.return_value = now

    msg1 = generate_message(topic="org.fedoraproject.prod.git.branch.valgrind.master")
    time1 = now - timedelta(days=2)
    msg1._properties.headers["sent-at"] = time1.isoformat()
    m.add(msg1)

    msg2 = generate_message(topic="org.fedoraproject.stg.fas.user.create")
    time2 = now - timedelta(days=1)
    msg2._properties.headers["sent-at"] = time2.isoformat()
    m.add(msg2)

    msg3 = generate_message(topic="org.fedoraproject.prod.git.receive.valgrind.master")
    time3 = now - timedelta(seconds=1)
    msg3._properties.headers["sent-at"] = time3.isoformat()
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, ["--timesince", "--human"])
    assert result.exit_code == 0, result.output

    assert json.loads(result.output) == ["1 day, 0:00:00", "0:00:01"]


def test_latest(datanommer_models, mock_config, mock_init):
    msg1 = generate_message(
        topic="org.fedoraproject.prod.git.branch.valgrind.master",
        body={"Message 1": "Message 1"},
    )
    time1 = datetime.now() - timedelta(days=2)
    msg1._properties.headers["sent-at"] = time1.isoformat()
    m.add(msg1)

    msg2 = generate_message(
        topic="org.fedoraproject.stg.fas.user.create", body={"Message 2": "Message 2"}
    )
    m.add(msg2)

    msg3 = generate_message(
        topic="org.fedoraproject.prod.git.receive.valgrind.master",
        body={"Message 3": "Message 3"},
    )
    m.add(msg3)

    runner = CliRunner()
    result = runner.invoke(datanommer.commands.latest, [])
    assert result.exit_code == 0, result.output

    json_object = json.loads(result.output)

    assert json_object[1]["git"]["body"] == {"Message 3": "Message 3"}
    assert json_object[0]["fas"]["body"] == {"Message 2": "Message 2"}
    assert len(json_object) == 2
