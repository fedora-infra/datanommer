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
import logging
import math
import traceback
import uuid

import fedmsg.encoding
import pkg_resources
from sqlalchemy import (
    between,
    cast,
    Column,
    create_engine,
    DateTime,
    DDL,
    event,
    func,
    Integer,
    not_,
    or_,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import scoped_session, sessionmaker, validates


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
    # ourselves from initializing twice.  That is only a problem is the code
    # calling us isn't consistent.
    if getattr(session, "_datanommer_initialized", None):
        log.warning("Session already initialized.  Bailing")
        return
    session._datanommer_initialized = True

    session.configure(bind=engine)
    DeclarativeBase.query = session.query_property()

    # Loads the alembic configuration and generates the version table, with
    # the most recent revision stamped as head
    if alembic_ini is not None:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    if create:
        DeclarativeBase.metadata.create_all(engine)


def add(envelope):
    """Take a dict-like fedmsg envelope and store the headers and message
    in the table.
    """
    message = envelope["body"]
    timestamp = message.get("timestamp", None)
    try:
        if timestamp:
            timestamp = datetime.datetime.utcfromtimestamp(timestamp)
        else:
            timestamp = datetime.datetime.utcnow()
    except Exception:
        pass

    headers = envelope.get("headers", None)
    msg_id = message.get("msg_id", None)
    if not msg_id and headers:
        msg_id = headers.get("message-id", None)
    if not msg_id:
        msg_id = str(timestamp.year) + "-" + str(uuid.uuid4())
    obj = Message(
        i=message.get("i", 0),
        msg_id=msg_id,
        topic=message["topic"],
        timestamp=timestamp,
        username=message.get("username", None),
        crypto=message.get("crypto", None),
        certificate=message.get("certificate", None),
        signature=message.get("signature", None),
    )

    obj.msg = message["msg"]
    obj.headers = headers

    usernames = fedmsg.meta.msg2usernames(message)
    packages = fedmsg.meta.msg2packages(message)

    # Do a little sanity checking on fedmsg.meta results
    if None in usernames:
        # Notify developers so they can fix msg2usernames
        log.error("NoneType found in usernames of %r" % msg_id)
        # And prune out the bad value
        usernames = [name for name in usernames if name is not None]

    if None in packages:
        # Notify developers so they can fix msg2packages
        log.error("NoneType found in packages of %r" % msg_id)
        # And prune out the bad value
        packages = [pkg for pkg in packages if pkg is not None]

    def _make_array(value):
        if value:
            return postgresql.array(value)
        else:
            # Cast it, otherwise you'll get:
            # sqlalchemy.exc.ProgrammingError: (psycopg2.errors.IndeterminateDatatype)
            # cannot determine type of empty array
            return cast(postgresql.array(value), postgresql.ARRAY(Unicode))

    obj.users = _make_array(usernames)
    obj.packages = _make_array(packages)

    try:
        session.add(obj)
        session.flush()
    except IntegrityError:
        log.warning(
            "Skipping message from %s with duplicate id: %s", message["topic"], msg_id
        )
        session.rollback()
        return
    # TODO -- can we avoid committing every time?
    session.commit()


def source_version_default(context):
    dist = pkg_resources.get_distribution("datanommer.models")
    return dist.version


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
    _msg = Column(UnicodeText, nullable=False)
    _headers = Column(UnicodeText)
    users = Column(postgresql.ARRAY(Unicode), index=True)
    packages = Column(postgresql.ARRAY(Unicode), index=True)

    @validates("topic")
    def get_category(self, key, topic):
        index = 2 if "VirtualTopic" in topic else 3
        try:
            self.category = topic.split(".")[index]
        except Exception:
            traceback.print_exc()
            self.category = "Unclassified"
        return topic

    @hybrid_property
    def msg(self):
        return fedmsg.encoding.loads(self._msg)

    @msg.setter
    def msg(self, dict_like_msg):
        self._msg = fedmsg.encoding.dumps(dict_like_msg)

    @hybrid_property
    def headers(self):
        hdrs = self._headers
        if hdrs:
            return fedmsg.encoding.loads(hdrs)
        else:
            return {}

    @headers.setter
    def headers(self, headers):
        if headers:
            self._headers = fedmsg.encoding.dumps(headers)
        else:
            self._headers = None

    @classmethod
    def from_msg_id(cls, msg_id):
        return cls.query.filter(cls.msg_id == msg_id).first()

    def __json__(self, request=None):
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
            users=self.users,
            packages=self.packages,
        )

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
            query = query.filter(or_(*(Message.users.any(u) for u in users)))

        if packages:
            query = query.filter(or_(*(Message.packages.any(p) for p in packages)))

        if categories:
            query = query.filter(
                or_(*(Message.category == category for category in categories))
            )

        if topics:
            query = query.filter(or_(*(Message.topic == topic for topic in topics)))

        if contains:
            query = query.filter(
                or_(*(Message._msg.like("%%%s%%" % contain) for contain in contains))
            )

        # And then the four negative filters as necessary
        if not_users:
            query = query.filter(not_(or_(*(Message.users.any(u) for u in not_users))))

        if not_packs:
            query = query.filter(
                not_(or_(*(Message.packages.any(p) for p in not_packs)))
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

        if rows_per_page is None:
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

    @classmethod
    def get_array(cls, name):
        return session.query(func.unnest(getattr(cls, name)).distinct())


def _setup_hypertable(table_class):
    event.listen(
        table_class.__table__,
        "after_create",
        DDL(f"SELECT create_hypertable('{table_class.__tablename__}', 'timestamp');"),
    )


_setup_hypertable(Message)
