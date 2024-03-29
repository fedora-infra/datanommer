import pytest
import sqlalchemy as sa
from click.testing import CliRunner

import datanommer.models as m
from datanommer.commands.extract_users import main as extract_users

from .utils import generate_bodhi_update_complete_message, generate_message


@pytest.fixture
def bodhi_message_db(datanommer_models):
    msg = generate_bodhi_update_complete_message()
    m.add(msg)
    m.session.execute(m.users_assoc_table.delete())
    m.session.commit()

    msg_in_db = m.Message.from_msg_id(msg.id)
    assert len(msg_in_db.users) == 0
    return msg_in_db


def test_extract_users(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users)

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) > 0
    assert {u.name for u in bodhi_message_db.users} == {"dudemcpants", "ryanlerch"}


def test_extract_users_topic(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--topic", "org.fedoraproject.stg.bodhi.update.comment"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) > 0
    assert {u.name for u in bodhi_message_db.users} == {"dudemcpants", "ryanlerch"}


def test_extract_users_wrong_topic(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--topic", "something.else"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) == 0


def test_extract_users_category(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--category", "bodhi"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) > 0
    assert {u.name for u in bodhi_message_db.users} == {"dudemcpants", "ryanlerch"}


def test_extract_users_wrong_category(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--category", "git"])

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    assert len(bodhi_message_db.users) == 0


def test_extract_users_topic_and_category(mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(extract_users, ["--category", "bodhi", "--topic", "some.topic"])
    assert result.exit_code != 0, result.output
    assert "Error: can't use both --topic and --category, choose one." in result.output


def test_extract_users_no_users(datanommer_models, mock_config, mock_init):
    msg = generate_message()
    m.add(msg)
    runner = CliRunner()
    result = runner.invoke(extract_users)

    assert result.exit_code == 0, result.output
    users_count = m.session.scalar(sa.select(sa.func.count(m.users_assoc_table.c.msg_id)))
    assert users_count == 0
    assert result.output == "Considering 1 message\n"
