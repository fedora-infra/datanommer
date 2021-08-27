import os

import pytest
from pytest_postgresql import factories
from sqlalchemy.orm import scoped_session

import datanommer.models as dm


@pytest.fixture(scope="session")
def postgresql_proc_with_timescaledb(postgresql_proc):
    with open(os.path.join(postgresql_proc.datadir, "postgresql.conf"), "a") as pgconf:
        pgconf.write("\nshared_preload_libraries = 'timescaledb'\n")
        pgconf.write("timescaledb.telemetry_level=off\n")
    postgresql_proc.stop()
    postgresql_proc.start()
    yield postgresql_proc


_inital_sql = os.path.abspath(os.path.join(os.path.dirname(__file__), "startup.sql"))
pgsql = factories.postgresql(
    "postgresql_proc_with_timescaledb",
    load=[_inital_sql],
)


@pytest.fixture()
def datanommer_db_url(pgsql):
    return (
        f"postgresql+psycopg2://{pgsql.info.user}:@"
        f"{pgsql.info.host}:{pgsql.info.port}"
        f"/{pgsql.info.dbname}"
    )


@pytest.fixture()
def datanommer_models(datanommer_db_url):
    dm.session = scoped_session(dm.maker)
    dm.init(datanommer_db_url, create=True)
    dm.User.clear_cache()
    dm.Package.clear_cache()
    yield dm.session
    dm.session.rollback()
    # engine = dm.session.get_bind()
    dm.session.close()
    # dm.DeclarativeBase.metadata.drop_all(engine)
