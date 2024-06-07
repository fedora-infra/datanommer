import pytest

import datanommer.commands


pytest_plugins = "datanommer.models.testing"


@pytest.fixture
def mock_init(mocker):
    # This is actually not very useful because init() checks a private attribute on the
    # session object to avoid being called twice. It just prevents a warning log.
    mocker.patch("datanommer.commands.m.init")


@pytest.fixture
def mock_config(mocker):
    mocker.patch.dict(
        datanommer.commands.utils.fedora_messaging_config.conf["consumer_config"],
        {
            "datanommer_sqlalchemy_url": "",
            "alembic_ini": None,
        },
    )
