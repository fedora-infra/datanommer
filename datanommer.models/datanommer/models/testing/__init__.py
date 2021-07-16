import os

import pytest
from pytest_postgresql import factories
from sqlalchemy.orm import scoped_session

import datanommer.models as dm


@pytest.fixture(scope="session")
def postgresql_proc_with_timescaledb(postgresql_proc):
    with open(os.path.join(postgresql_proc.datadir, "postgresql.conf"), "a") as pgconf:
        pgconf.write("\nshared_preload_libraries = 'timescaledb'\n")
    postgresql_proc.stop()
    postgresql_proc.start()
    yield postgresql_proc


_inital_sql = os.path.abspath(os.path.join(os.path.dirname(__file__), "startup.sql"))
pgsql = factories.postgresql(
    "postgresql_proc_with_timescaledb",
    load=[_inital_sql],
)


@pytest.fixture()
def fedmsg_config(pgsql):
    import fedmsg.config
    import fedmsg.meta

    url = (
        f"postgresql+psycopg2://{pgsql.info.user}:@"
        f"{pgsql.info.host}:{pgsql.info.port}"
        f"/{pgsql.info.dbname}"
    )
    config = fedmsg.config.load_config(invalidate_cache=True)
    config["datanommer.enabled"] = True
    # conf.load_config({"datanommer.sqlalchemy.url": url})
    config["datanommer.sqlalchemy.url"] = url
    fedmsg.meta.make_processors(**config)
    return config


@pytest.fixture()
def datanommer_models(fedmsg_config):
    dm.session = scoped_session(dm.maker)
    dm.init(fedmsg_config["datanommer.sqlalchemy.url"], create=True)
    yield dm.session
    dm.session.rollback()
    # engine = dm.session.get_bind()
    dm.session.close()
    # dm.DeclarativeBase.metadata.drop_all(engine)
