from sqlalchemy import create_engine
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    ForeignKey,
    UnicodeText,
)

from sqlalchemy.orm import (
    sessionmaker,
    scoped_session,
    relationship,
    backref,
)

from sqlalchemy import or_, between

from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy.schema import Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

import pkg_resources

import math
import datetime
import fedmsg.encoding

maker = sessionmaker()
session = scoped_session(maker)

DeclarativeBase = declarative_base()
DeclarativeBase.query = session.query_property()

import logging
log = logging.getLogger("datanommer")


def init(uri=None, alembic_ini=None, engine=None, create=False):
    """ Initialize a connection.  Create tables if requested."""

    if uri and engine:
        raise ValueError("uri and engine cannot both be specified")

    if uri is None and not engine:
        uri = 'sqlite:////tmp/datanommer.db'
        log.warning("No db uri given.  Using %r" % uri)

    if uri and not engine:
        engine = create_engine(uri)

    session.configure(bind=engine)
    DeclarativeBase.query = session.query_property()

    # Loads the alembic configuration and generates the version table, with
    # the most recent revision stamped as head
    if alembic_ini is not None:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    if create:
        DeclarativeBase.metadata.create_all(engine)


def add(message):
    """ Take a dict-like fedmsg message and store it in the table.
    """
    timestamp = message['timestamp']
    try:
        timestamp = datetime.datetime.fromtimestamp(timestamp)
    except Exception:
        pass

    obj = Message(
        i=message['i'],
        msg_id=message.get('msg_id', None),
        topic=message['topic'],
        timestamp=timestamp,
        certificate=message.get('certificate', None),
        signature=message.get('signature', None),
    )

    obj.msg = message['msg']

    session.add(obj)

    usernames = fedmsg.meta.msg2usernames(message)
    packages = fedmsg.meta.msg2packages(message)
    for username in usernames:
        user = session.query(User).get(username)

        if not user:
            user = User(name=username)

        obj.users.append(user)

    for package_name in packages:
        package = session.query(Package).get(package_name)

        if not package:
            package = Package(name=package_name)

        obj.packages.append(package)

    # TODO -- can we avoid committing every time?
    session.flush()
    session.commit()


def source_version_default(context):
    dist = pkg_resources.get_distribution("datanommer.models")
    return dist.version


class BaseMessage(object):
    id = Column(Integer, primary_key=True)
    msg_id = Column(UnicodeText, nullable=True, unique=True, default=None)
    i = Column(Integer, nullable=False)
    topic = Column(UnicodeText, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    certificate = Column(UnicodeText)
    signature = Column(UnicodeText)
    category = Column(UnicodeText, nullable=False)
    source_name = Column(UnicodeText, default=u"datanommer")
    source_version = Column(UnicodeText, default=source_version_default)
    _msg = Column(UnicodeText, nullable=False)

    @validates('topic')
    def get_category(self, key, topic):
        import fedmsg.config
        import fedmsg.meta

        config = fedmsg.config.load_config([], None)
        fedmsg.meta.make_processors(**config)

        filters=[]
        for f in fedmsg.meta.processors:
            filters.append(f.__name__.lower())

        for f in filters:
            if f in topic:
                self.category = f
                break
            else:
                self.category = 'Unclassified'

        return topic

    @hybrid_property
    def msg(self):
        return fedmsg.encoding.loads(self._msg)

    @msg.setter
    def msg(self, dict_like_msg):
        self._msg = fedmsg.encoding.dumps(dict_like_msg)

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
            msg=self.msg,
            source_name=self.source_name,
            source_version=self.source_version,
        )

user_assoc_table = Table('user_messages', DeclarativeBase.metadata,
    Column('username', UnicodeText, ForeignKey('user.name')),
    Column('msg', Integer, ForeignKey('messages.id'))
)

pack_assoc_table = Table('package_messages', DeclarativeBase.metadata,
    Column('package', UnicodeText, ForeignKey('package.name')),
    Column('msg', Integer, ForeignKey('messages.id'))
)


class User(DeclarativeBase):
    __tablename__ = 'user'
    name = Column(UnicodeText, primary_key=True)

    @classmethod
    def get_or_create(cls, name):
        try:
            return cls.query.filter_by(name=name).one()
        except NoResultFound:
            obj = cls(name=name)
            session.add(obj)
            return obj


class Package(DeclarativeBase):
    __tablename__ = 'package'
    name = Column(UnicodeText, primary_key=True)

    @classmethod
    def get_or_create(cls, name):
        try:
            return cls.query.filter_by(name=name).one()
        except NoResultFound:
            obj = cls(name=name)
            session.add(obj)
            return obj


class Message(DeclarativeBase, BaseMessage):
    __tablename__ = "messages"
    users = relationship("User", secondary=user_assoc_table,
                         backref=backref('messages'))
    packages = relationship("Package", secondary=pack_assoc_table,
                            backref=backref('messages'))

    @classmethod
    def grep(cls, start=None, end=None,
             page=1, rows_per_page=100,
             order="asc", msg_id=None,
             users=None, packages=None,
             categories=None, topics=None,
             defer=False):
        """ Flexible query interface for messages.

        Arguments are filters.  start and end should be :mod:`datetime` objs.

        Other filters should be lists of strings.  They are applied in a
        conjunctive-normal-form (CNF) kind of way

        for example, the following::

          users = ['ralph', 'lmacken']
          categories = ['bodhi', 'wiki']

        should return messages where

          (user=='ralph' OR user=='lmacken') AND
          (category=='bodhi' OR category=='wiki')

        If the `defer` argument evaluates to True, the query won't actually
        be executed, but a SQLAlchemy query object returned instead.
        """

        users = users or []
        packages = packages or []
        categories = categories or []
        topics = topics or []

        query = Message.query

        # A little argument validation.  We could provide some defaults in
        # these mixed cases.. but instead we'll just leave it up to our caller.
        if (start != None and end == None) or (end != None and start == None):
            raise ValueError("Either both start and end must be specified "
                             "or neither must be specified")

        if start and end:
            query = query.filter(between(Message.timestamp, start, end))

        if msg_id:
            query = query.filter(Message.msg_id == msg_id)

        query = query.filter(or_(
            *[Message.users.any(User.name == u) for u in users]
        ))
        query = query.filter(or_(
            *[Message.packages.any(Package.name == p) for p in packages]
        ))
        query = query.filter(or_(
            *[Message.category == category for category in categories]
        ))
        query = query.filter(or_(
            *[Message.topic == topic for topic in topics]
        ))

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

models = frozenset((
    v for k, v in locals().items()
    if (
        isinstance(v, type) and
        issubclass(v, BaseMessage) and
        k is not "BaseMessage"
    )
))
