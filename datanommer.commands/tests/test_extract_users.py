import datetime
import io
from unittest.mock import Mock

import pytest
import sqlalchemy as sa
from click import progressbar
from click.testing import CliRunner

import datanommer.models as m
from datanommer.commands.extract_users import main as extract_users

from .utils import generate_bodhi_update_complete_message, generate_message


@pytest.fixture
def bodhi_message_db(datanommer_models):
    msg = generate_bodhi_update_complete_message()
    m.add(msg)
    m.session.execute(m.users_assoc_table.delete())
    msg_in_db = m.Message.from_msg_id(msg.id)
    msg_in_db.agent_name = None
    m.session.commit()

    m.session.refresh(msg_in_db)
    assert len(msg_in_db.users) == 0
    assert msg_in_db.agent_name is None
    return msg_in_db


@pytest.fixture(autouse=True)
def no_expunge(datanommer_models, monkeypatch):
    monkeypatch.setattr(m.session, "expunge_all", Mock(name="expunge_all"))
    monkeypatch.setattr(m.session, "expunge", Mock(name="expunge"))


def test_extract_users(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--debug", "usernames"])

    assert result.exit_code == 0, result.output
    expected_output = (
        "Counting messages...\n"
        "Considering 1 message\n\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
        f"Usernames for message {bodhi_message_db.msg_id} of topic {bodhi_message_db.topic}: "
        "dudemcpants, ryanlerch\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
    )
    assert result.output == expected_output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) > 0
    assert {u.name for u in bodhi_message_db.users} == {"dudemcpants", "ryanlerch"}


def test_extract_users_topic(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(
        extract_users, ["--topic", "org.fedoraproject.stg.bodhi.update.comment", "usernames"]
    )

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) > 0
    assert {u.name for u in bodhi_message_db.users} == {"dudemcpants", "ryanlerch"}


def test_extract_users_wrong_topic(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--topic", "something.else", "usernames"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) == 0


def test_extract_users_category(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--category", "bodhi", "usernames"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) > 0
    assert {u.name for u in bodhi_message_db.users} == {"dudemcpants", "ryanlerch"}


def test_extract_users_wrong_category(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--category", "git", "usernames"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) == 0


def test_extract_users_topic_and_category(mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(
        extract_users, ["--category", "bodhi", "--topic", "some.topic", "usernames"]
    )
    assert result.exit_code != 0, result.output
    assert "Error: can't use both --topic and --category, choose one." in result.output


def test_extract_users_skipped_topic(bodhi_message_db, mock_config, mock_init):
    bodhi_message_db.topic = "org.release-monitoring.prod.anitya.project.version.update"
    m.session.commit()

    runner = CliRunner()
    result = runner.invoke(extract_users, ["usernames"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) == 0


def test_extract_users_no_users(datanommer_models, mock_config, mock_init):
    msg = generate_message()
    # change the schema header or the script won't pick it up
    msg._headers["fedora_messaging_schema"] = "testing"
    m.add(msg)
    runner = CliRunner()
    result = runner.invoke(extract_users, ["usernames"])

    assert result.exit_code == 0, result.output
    users_count = m.session.scalar(sa.select(sa.func.count(m.users_assoc_table.c.msg_id)))
    assert users_count == 0
    start = datetime.datetime.fromisoformat(msg._headers["sent-at"]).astimezone()
    start = str(start).split("+")[0]
    assert result.output == (
        "Counting messages...\n"
        "Considering 1 message\n\n"
        f"Working on 10000 messages sent after {start}\n"
        f"Working on 10000 messages sent after {start}\n"
    )


def test_extract_start(datanommer_models, mock_config, mock_init):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    msg = generate_bodhi_update_complete_message()
    # Set the message to have happenned 3 days ago
    msg._properties.headers["sent-at"] = (now - datetime.timedelta(days=3)).isoformat()
    m.add(msg)
    m.session.execute(m.users_assoc_table.delete())
    m.session.commit()

    runner = CliRunner()
    # Only look at messages from yesterday on
    result = runner.invoke(
        extract_users,
        ["--start", (now - datetime.timedelta(days=1)).strftime(r"%Y-%m-%d"), "usernames"],
    )

    assert result.exit_code == 0, result.output
    # Message must not have had users set
    users_count = m.session.scalar(sa.select(sa.func.count(m.users_assoc_table.c.msg_id)))
    assert users_count == 0
    assert result.output == "Counting messages...\nNo messages matched.\n"


def test_extract_end(bodhi_message_db, mock_config, mock_init):
    now = datetime.datetime.now()
    runner = CliRunner()
    # Only look at messages from yesterday on
    result = runner.invoke(
        extract_users,
        ["--end", (now - datetime.timedelta(days=1)).strftime(r"%Y-%m-%d"), "usernames"],
    )

    assert result.exit_code == 0, result.output
    # Message must not have had users set
    users_count = m.session.scalar(sa.select(sa.func.count(m.users_assoc_table.c.msg_id)))
    assert users_count == 0
    assert result.output == "Counting messages...\nNo messages matched.\n"


def test_extract_force_schema(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--force-schema", "base.message", "usernames"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) == 0


def test_extract_invalid_message(bodhi_message_db, mock_config, mock_init):
    bodhi_message_db.msg = "this is invalid"
    m.session.commit()

    runner = CliRunner()
    result = runner.invoke(extract_users, ["usernames"])

    assert result.exit_code == 0, result.output
    assert result.output == (
        "Counting messages...\n"
        "Considering 1 message\n\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
        f"Could not load message {bodhi_message_db.msg_id} on topic "
        f"{bodhi_message_db.topic}: 'this is invalid' is not of type 'object'\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
    )

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) == 0


def test_extract_agent(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["agent"])

    assert result.exit_code == 0, result.output
    assert result.output == (
        "Counting messages...\n"
        "Considering 1 message\n\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
    )
    m.session.refresh(bodhi_message_db)
    assert bodhi_message_db.agent_name == "dudemcpants"


def test_extract_agent_with(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--debug", "agent"])

    assert result.exit_code == 0, result.output
    expected_output = (
        "Counting messages...\n"
        "Considering 1 message\n\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
        f"Agent for message {bodhi_message_db.msg_id} of topic {bodhi_message_db.topic}: "
        "dudemcpants\n"
        f"Working on 10000 messages sent after {bodhi_message_db.timestamp}\n"
    )
    assert result.output == expected_output


def test_extract_agent_no_users(datanommer_models, mock_config, mock_init):
    msg = generate_message()
    # change the schema header or the script won't pick it up
    msg._headers["fedora_messaging_schema"] = "testing"
    m.add(msg)
    runner = CliRunner()
    result = runner.invoke(extract_users, ["agent"])

    assert result.exit_code == 0, result.output
    msg_in_db = m.Message.from_msg_id(msg.id)
    assert msg_in_db.agent_name is None
    assert result.output == (
        "Counting messages...\n"
        "Considering 1 message\n\n"
        f"Working on 10000 messages sent after {msg_in_db.timestamp}\n"
        f"Working on 10000 messages sent after {msg_in_db.timestamp}\n"
    )


def test_extract_is_tty(bodhi_message_db, mock_config, mock_init, mocker):
    output = io.StringIO()
    mocker.patch.object(output, "isatty", lambda: True)
    mocker.patch(
        "datanommer.commands.utils.click.progressbar", lambda **kw: progressbar(file=output, **kw)
    )
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--debug", "usernames"])

    assert result.exit_code == 0, result.output
    expected_output = (
        "Counting messages...\n"
        "Considering 1 message\n"
        f"Usernames for message {bodhi_message_db.msg_id} of topic {bodhi_message_db.topic}: "
        "dudemcpants, ryanlerch\n"
    )
    assert result.output == expected_output
