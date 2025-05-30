from sqlalchemy import DDL, func, select, text
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement


TIME_INTERVAL = "1 year"


class CreateMaterializedView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


@compiler.compiles(CreateMaterializedView)
def _create_view(element, compiler, **kw):
    selectable = compiler.sql_compiler.process(element.selectable, literal_binds=True)
    return f"CREATE MATERIALIZED VIEW IF NOT EXISTS {element.name} AS {selectable}"


def get_selectable():
    """Factory function to create the selectable query for materialized view."""
    from . import Message

    return (
        select(
            Message.topic,
            func.count().label("message_count"),
            func.min(Message.timestamp).label("earliest"),
            func.max(Message.timestamp).label("latest"),
        )
        .where(Message.timestamp >= text(f"NOW() - INTERVAL '{TIME_INTERVAL}'"))
        .group_by(Message.topic)
    )


def refresh_recent_topics(connection):
    """Standalone refresh function that can be called from cron.

    Args:
        connection: SQLAlchemy connection object
    """
    connection.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY recent_topics"))


def create_view(connection):
    """Create the recent_topics materialized view with proper indexes."""

    selectable = get_selectable()

    # Create the materialized view
    connection.execute(CreateMaterializedView("recent_topics", selectable))

    # Create unique index on topic
    connection.execute(
        DDL("CREATE UNIQUE INDEX IF NOT EXISTS uq_recent_topics_topic " "ON recent_topics (topic)"),
    )

    # Create index on message_count for sorting
    connection.execute(
        DDL(
            "CREATE INDEX IF NOT EXISTS ix_recent_topics_message_count "
            "ON recent_topics (message_count)"
        )
    )
