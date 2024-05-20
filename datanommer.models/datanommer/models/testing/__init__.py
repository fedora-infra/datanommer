import pytest
import sqlalchemy as sa
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy.orm import scoped_session

import datanommer.models as dm


postgresql_proc = factories.postgresql_proc(
    postgres_options="-c shared_preload_libraries=timescaledb -c timescaledb.telemetry_level=off",
)


@pytest.fixture(scope="session")
def datanommer_db_url(postgresql_proc):
    return (
        f"postgresql+psycopg2://{postgresql_proc.user}:@"
        f"{postgresql_proc.host}:{postgresql_proc.port}"
        f"/{postgresql_proc.dbname}"
    )


@pytest.fixture(scope="session")
def datanommer_db_engine(postgresql_proc, datanommer_db_url):
    with DatabaseJanitor(
        user=postgresql_proc.user,
        host=postgresql_proc.host,
        port=postgresql_proc.port,
        dbname=postgresql_proc.dbname,
        # Don't use a template database
        # template_dbname=postgresql_proc.template_dbname,
        version=postgresql_proc.version,
    ):
        engine = sa.create_engine(datanommer_db_url, future=True)
        # Renew the global object, dm.init checks a custom attribute
        dm.session = scoped_session(dm.maker)
        dm.init(engine=engine, create=True)
        yield engine
        engine.dispose()


@pytest.fixture()
def datanommer_db(datanommer_db_url, datanommer_db_engine):
    for table in reversed(dm.DeclarativeBase.metadata.sorted_tables):
        dm.session.execute(table.delete())
    dm.session.commit()
    yield datanommer_db_engine


@pytest.fixture()
def datanommer_models(datanommer_db):
    dm.User.clear_cache()
    dm.Package.clear_cache()
    yield dm.session
    dm.session.rollback()
