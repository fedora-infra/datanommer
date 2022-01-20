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
import datetime
import json
import logging
import math
import traceback
import uuid
from warnings import warn

import pkg_resources
from sqlalchemy import (
    and_,
    between,
    Column,
    create_engine,
    DateTime,
    DDL,
    event,
    ForeignKey,
    Integer,
    not_,
    or_,
    String,
    Table,
    TypeDecorator,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    scoped_session,
    sessionmaker,
    validates,
)
from sqlalchemy.sql import operators


try:
    from psycopg2.errors import UniqueViolation
except ImportError:  # pragma: no cover
    from psycopg2.errorcodes import lookup as lookup_error

    UniqueViolation = lookup_error("23505")


log = logging.getLogger("datanommer")

maker = sessionmaker()
session = scoped_session(maker)

DeclarativeBase = declarative_base()
DeclarativeBase.query = session.query_property()


def init(uri=None, alembic_ini=None, engine=None, create=False):
    """Initialize a connection.  Create tables if requested."""

    if uri and engine:
        raise ValueError("uri and engine cannot both be specified")

    if uri is None and not engine:
        raise ValueError("One of uri or engine must be specified")

    if uri and not engine:
        engine = create_engine(uri)

    # We need to hang our own attribute on the sqlalchemy session to stop
    # ourselves from initializing twice.  That is only a problem if the code
    # calling us isn't consistent.
    if getattr(session, "_datanommer_initialized", None):
        log.warning("Session already initialized.  Bailing")
        return
    session._datanommer_initialized = True

    session.configure(bind=engine)
    DeclarativeBase.query = session.query_property()

    if create:
        session.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        DeclarativeBase.metadata.create_all(engine)
        # Loads the alembic configuration and generates the version table, with
        # the most recent revision stamped as head
        if alembic_ini is not None:  # pragma: no cover
            from alembic import command
            from alembic.config import Config

            alembic_cfg = Config(alembic_ini)
            command.stamp(alembic_cfg, "head")


def add(message):
    """Take a the fedora-messaging Message and store in the message
    table.
    """
    headers = message._properties.headers
    sent_at = headers.get("sent-at", None)

    if sent_at:
        # fromisoformat doesn't parse Z suffix (yet) see:
        # https://discuss.python.org/t/parse-z-timezone-suffix-in-datetime/2220
        try:
            sent_at = datetime.datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
        except ValueError:
            log.exception("Failed to parse sent-at timestamp value")
            return
    else:
        sent_at = datetime.datetime.utcnow()

    # Workaround schemas misbehaving
    try:
        usernames = message.usernames
    except Exception:
        log.exception(
            "Could not get the list of users from a message on %s with id %s",
            message.topic,
            message.id,
        )
        usernames = []
    try:
        packages = message.packages
    except Exception:
        log.exception(
            "Could not get the list of packages from a message on %s with id %s",
            message.topic,
            message.id,
        )
        packages = []

    Message.create(
        i=0,
        msg_id=message.id,
        topic=message.topic,
        timestamp=sent_at,
        msg=message.body,
        headers=headers,
        users=usernames,
        packages=packages,
    )

    session.commit()


def source_version_default(context):
    dist = pkg_resources.get_distribution("datanommer.models")
    return dist.version


# https://docs.sqlalchemy.org/en/14/core/custom_types.html#marshal-json-strings


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = UnicodeText

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

    def coerce_compared_value(self, op, value):
        # https://docs.sqlalchemy.org/en/14/core/custom_types.html#dealing-with-comparison-operations
        if op in (operators.like_op, operators.not_like_op):
            return String()
        else:
            return self


users_assoc_table = Table(
    "users_messages",
    DeclarativeBase.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("msg_id", Integer, primary_key=True, index=True),
    Column("msg_timestamp", DateTime, primary_key=True, index=True),
)

packages_assoc_table = Table(
    "packages_messages",
    DeclarativeBase.metadata,
    Column("package_id", ForeignKey("packages.id"), primary_key=True),
    Column("msg_id", Integer, primary_key=True, index=True),
    Column("msg_timestamp", DateTime, primary_key=True, index=True),
)


class Message(DeclarativeBase):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("msg_id", "timestamp"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    msg_id = Column(Unicode, nullable=True, default=None, index=True)
    i = Column(Integer, nullable=False)
    topic = Column(Unicode, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, primary_key=True)
    certificate = Column(UnicodeText)
    signature = Column(UnicodeText)
    category = Column(Unicode, nullable=False, index=True)
    username = Column(Unicode)
    crypto = Column(UnicodeText)
    source_name = Column(Unicode, default="datanommer")
    source_version = Column(Unicode, default=source_version_default)
    msg = Column(JSONEncodedDict, nullable=False)
    headers = Column(postgresql.JSONB(none_as_null=True))
    users = relationship(
        "User",
        secondary=users_assoc_table,
        backref="messages",
        primaryjoin=lambda: and_(
            Message.id == users_assoc_table.c.msg_id,
            Message.timestamp == users_assoc_table.c.msg_timestamp,
        ),
    )
    packages = relationship(
        "Package",
        secondary=packages_assoc_table,
        backref="messages",
        primaryjoin=lambda: and_(
            Message.id == packages_assoc_table.c.msg_id,
            Message.timestamp == packages_assoc_table.c.msg_timestamp,
        ),
    )

    @validates("topic")
    def get_category(self, key, topic):
        """Update the category when the topic is set.

        The method seems... unnatural. But even zzzeek says it's OK to do it:
        https://stackoverflow.com/a/6442201
        """
        index = 2 if "VirtualTopic" in topic else 3
        try:
            self.category = topic.split(".")[index]
        except Exception:
            traceback.print_exc()
            self.category = "Unclassified"
        return topic

    @classmethod
    def create(cls, **kwargs):
        users = kwargs.pop("users")
        packages = kwargs.pop("packages")
        if not kwargs.get("msg_id"):
            log.info("Message on %s was received without a msg_id", kwargs["topic"])
            kwargs["msg_id"] = str(uuid.uuid4())
        obj = cls(**kwargs)

        try:
            session.add(obj)
            session.flush()
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                log.warning(
                    "Skipping message from %s with duplicate id: %s",
                    kwargs["topic"],
                    kwargs["msg_id"],
                )
            else:
                log.exception(
                    "Unknown Integrity Error: message %s with id %s",
                    kwargs["topic"],
                    kwargs["msg_id"],
                )
            session.rollback()
            return

        obj._insert_list(User, users_assoc_table, users)
        obj._insert_list(Package, packages_assoc_table, packages)

    def _insert_list(self, rel_class, assoc_table, values):
        if not values:
            return
        assoc_col_name = assoc_table.c[0].name
        insert_values = []
        for name in set(values):
            attr_obj = rel_class.get_or_create(name)
            # This would normally be a simple "obj.[users|packages].append(name)" kind
            # of statement, but here we drop down out of sqlalchemy's ORM and into the
            # sql abstraction in order to gain a little performance boost.
            insert_values.append(
                {
                    assoc_col_name: attr_obj.id,
                    "msg_id": self.id,
                    "msg_timestamp": self.timestamp,
                }
            )
        session.execute(assoc_table.insert(), insert_values)
        session.flush()

    @classmethod
    def from_msg_id(cls, msg_id):
        return cls.query.filter(cls.msg_id == msg_id).first()

    def as_dict(self, request=None):
        return dict(
            i=self.i,
            msg_id=self.msg_id,
            topic=self.topic,
            timestamp=self.timestamp,
            certificate=self.certificate,
            signature=self.signature,
            username=self.username,
            crypto=self.crypto,
            msg=self.msg,
            headers=self.headers,
            source_name=self.source_name,
            source_version=self.source_version,
            users=list(sorted(u.name for u in self.users)),
            packages=list(sorted(p.name for p in self.packages)),
        )

    def as_fedora_message_dict(self):
        headers = self.headers or {}
        if "sent-at" not in headers:
            headers["sent-at"] = self.timestamp.astimezone(
                datetime.timezone.utc
            ).isoformat()
        return dict(
            body=self.msg,
            headers=headers,
            id=self.msg_id,
            queue=None,
            topic=self.topic,
        )

    def __json__(self, request=None):
        warn(
            "The __json__() method has been renamed to as_dict(), and will be removed "
            "in the next major version",
            DeprecationWarning,
        )
        return self.as_dict(request)

    @classmethod
    def grep(
        cls,
        start=None,
        end=None,
        page=1,
        rows_per_page=100,
        order="asc",
        msg_id=None,
        users=None,
        not_users=None,
        packages=None,
        not_packages=None,
        categories=None,
        not_categories=None,
        topics=None,
        not_topics=None,
        contains=None,
        defer=False,
    ):
        """Flexible query interface for messages.

        Arguments are filters.  start and end should be :mod:`datetime` objs.

        Other filters should be lists of strings.  They are applied in a
        conjunctive-normal-form (CNF) kind of way

        for example, the following::

          users = ['ralph', 'lmacken']
          categories = ['bodhi', 'wiki']

        should return messages where

          (user=='ralph' OR user=='lmacken') AND
          (category=='bodhi' OR category=='wiki')

        Furthermore, you can use a negative version of each argument.

            users = ['ralph']
            not_categories = ['bodhi', 'wiki']

        should return messages where

            (user == 'ralph') AND
            NOT (category == 'bodhi' OR category == 'wiki')

        ----

        If the `defer` argument evaluates to True, the query won't actually
        be executed, but a SQLAlchemy query object returned instead.
        """

        users = users or []
        not_users = not_users or []
        packages = packages or []
        not_packs = not_packages or []
        categories = categories or []
        not_cats = not_categories or []
        topics = topics or []
        not_topics = not_topics or []
        contains = contains or []

        query = Message.query

        # A little argument validation.  We could provide some defaults in
        # these mixed cases.. but instead we'll just leave it up to our caller.
        if (start is not None and end is None) or (end is not None and start is None):
            raise ValueError(
                "Either both start and end must be specified "
                "or neither must be specified"
            )

        if start and end:
            query = query.filter(between(Message.timestamp, start, end))

        if msg_id:
            query = query.filter(Message.msg_id == msg_id)

        # Add the four positive filters as necessary
        if users:
            query = query.filter(
                or_(*(Message.users.any(User.name == u) for u in users))
            )

        if packages:
            query = query.filter(
                or_(*(Message.packages.any(Package.name == p) for p in packages))
            )

        if categories:
            query = query.filter(
                or_(*(Message.category == category for category in categories))
            )

        if topics:
            query = query.filter(or_(*(Message.topic == topic for topic in topics)))

        if contains:
            query = query.filter(
                or_(*(Message.msg.like(f"%{contain}%") for contain in contains))
            )

        # And then the four negative filters as necessary
        if not_users:
            query = query.filter(
                not_(or_(*(Message.users.any(User.name == u) for u in not_users)))
            )

        if not_packs:
            query = query.filter(
                not_(or_(*(Message.packages.any(Package.name == p) for p in not_packs)))
            )

        if not_cats:
            query = query.filter(
                not_(or_(*(Message.category == category for category in not_cats)))
            )

        if not_topics:
            query = query.filter(
                not_(or_(*(Message.topic == topic for topic in not_topics)))
            )

        # Finally, tag on our pagination arguments
        total = query.count()
        query = query.order_by(getattr(Message.timestamp, order)())

        if not rows_per_page:
            pages = 1
        else:
            pages = int(math.ceil(total / float(rows_per_page)))
            query = query.offset(rows_per_page * (page - 1)).limit(rows_per_page)

        if defer:
            return total, page, query
        else:
            # Execute!
            messages = query.all()
            return total, pages, messages


class NamedSingleton:

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(UnicodeText, index=True, unique=True)

    @classmethod
    def get_or_create(cls, name):
        """
        Return the instance of the class with the specified name. If it doesn't
        already exist, create it.
        """
        # Use an in-memory cache to speed things up.
        if name in cls._cache:
            # If we cache the instance, SQLAlchemy will run this query anyway because the instance
            # will be from a different transaction. So just cache the id.
            return cls.query.get(cls._cache[name])
        obj = cls.query.filter_by(name=name).one_or_none()
        if obj is None:
            obj = cls(name=name)
            session.add(obj)
            session.flush()
        cls._cache[name] = obj.id
        return obj

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()


class User(DeclarativeBase, NamedSingleton):
    __tablename__ = "users"
    _cache = {}


class Package(DeclarativeBase, NamedSingleton):
    __tablename__ = "packages"
    _cache = {}


def _setup_hypertable(table_class):
    event.listen(
        table_class.__table__,
        "after_create",
        DDL(f"SELECT create_hypertable('{table_class.__tablename__}', 'timestamp');"),
    )


_setup_hypertable(Message)


# Set the version
try:  # pragma: no cover
    import importlib.metadata

    __version__ = importlib.metadata.version("datanommer.models")
except ImportError:  # pragma: no cover
    try:
        __version__ = pkg_resources.get_distribution("datanommer.models").version
    except pkg_resources.DistributionNotFound:
        # The app is not installed, but the flask dev server can run it nonetheless.
        __version__ = None
