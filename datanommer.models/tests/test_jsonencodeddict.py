import pytest
from sqlalchemy import Column, create_engine, Integer, MetaData, Table
from sqlalchemy.sql import select

from datanommer.models import JSONEncodedDict


@pytest.fixture
def connection():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        yield connection


@pytest.fixture
def table(connection):
    metadata = MetaData()
    table = Table(
        "test_table",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("data", JSONEncodedDict),
    )
    metadata.create_all(connection)
    yield table
    metadata.drop_all(connection)


def test_jsonencodeddict(connection, table):
    connection.execute(table.insert().values(data={"foo": "bar"}))
    # Check that it's stored as a string
    for row in connection.execute("SELECT data FROM test_table"):
        assert row["data"] == '{"foo": "bar"}'
    # Check that SQLAlchemy retrieves it as a dict
    for row in connection.execute(select(table.c.data)):
        assert row["data"] == {"foo": "bar"}


def test_jsonencodeddict_null(connection, table):
    # Make sure NULL values are supported
    connection.execute(table.insert().values(data=None))
    for row in connection.execute(select(table.c.data)):
        assert row["data"] is None


def test_jsonencodeddict_compare(connection, table):
    # Make sure NULL values are supported
    connection.execute(table.insert().values(data={"foo": "bar"}))
    for row in connection.execute(
        select(table.c.data).filter(table.c.data == {"foo": "bar"})
    ):
        assert row["data"] == {"foo": "bar"}


def test_jsonencodeddict_compare_like(connection, table):
    # Make sure NULL values are supported
    connection.execute(table.insert().values(data={"foo": "bar"}))
    for row in connection.execute(
        select(table.c.data).filter(table.c.data.like("%foo%"))
    ):
        assert row["data"] == {"foo": "bar"}
