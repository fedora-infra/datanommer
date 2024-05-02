from unittest.mock import Mock

import pytest
from click.testing import CliRunner

import datanommer.models as m
from datanommer.commands.populate_json import main as populate_json

from .utils import generate_bodhi_update_complete_message


@pytest.fixture
def bodhi_message_db(datanommer_models):
    msg = generate_bodhi_update_complete_message()
    m.add(msg)
    msg_in_db = m.Message.from_msg_id(msg.id)
    msg_in_db.msg_raw = msg_in_db.msg_json
    msg_in_db.msg_json = None
    m.session.commit()
    m.session.refresh(msg_in_db)
    assert msg_in_db.msg_json is None
    return msg_in_db


@pytest.fixture(autouse=True)
def no_expunge(datanommer_models, monkeypatch):
    monkeypatch.setattr(m.session, "expunge_all", Mock(name="expunge_all"))
    monkeypatch.setattr(m.session, "expunge", Mock(name="expunge"))


def test_populate_json(bodhi_message_db, mock_config, mock_init):
    runner = CliRunner()
    result = runner.invoke(populate_json)

    assert result.exit_code == 0, result.output

    m.session.refresh(bodhi_message_db)
    print(bodhi_message_db.msg_json)
    assert bodhi_message_db.msg_json is not None
    assert bodhi_message_db.msg_raw is None
    total, _pages, _messages = m.Message.grep(jsons=['$.comment.user.name == "dudemcpants"'])
    assert total == 1
    assert _messages == [bodhi_message_db]


def test_populate_json_no_message(monkeypatch, mock_config, mock_init):
    monkeypatch.setattr(m.session, "execute", Mock(name="execute"))
    runner = CliRunner()
    result = runner.invoke(populate_json)
    assert result.exit_code == 0, result.output
    assert result.output == "No message to populate.\n"
    m.session.execute.assert_not_called()
