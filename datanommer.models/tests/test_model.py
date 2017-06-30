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
import copy
import datetime
import pprint
import sqlalchemy
import sqlalchemy.exc
import unittest
import requests

from sqlalchemy.orm import scoped_session

from nose.tools import raises
from nose.tools import eq_

import datanommer.models

# Set this to false to use faitout
USE_SQLITE = True  # False

filename = ":memory:"

scm_message = {
"body": {
    "i": 1,
    "timestamp": 1344350850.8867381,
    "topic": "org.fedoraproject.prod.git.receive.valgrind.master",
    "msg": {
        "commit": {
            "stats": {
                "files": {
                    "valgrind.spec": {
                        "deletions": 2,
                        "lines": 3,
                        "insertions": 1
                    }
                },
                "total": {
                    "deletions": 2,
                    "files": 1,
                    "insertions": 1,
                    "lines": 3
                }
            },
            "name": "Mark Wielaard",
            "rev": "7a98f80d9b61ce167e4ef8129c81ed9284ecf4e1",
            "summary": "Clear CFLAGS CXXFLAGS LDFLAGS.",
            "message": """Clear CFLAGS CXXFLAGS LDFLAGS.
            This is a bit of a hammer.""",
            "email": "mjw@redhat.com",
            "branch": "master",
            "username": "mjw",
        }
    },
    "signature": "blah",
    "certificate": "blah",
    "username": "mjw",
}
}


github_message = {
"body": {
    "i": 2,
    "msg": {
        "compare": "https://github.com/ralphbean/apps.fp.o",
        "fas_usernames": {},
        "hook": {
            "active": True,
            "config": {
                "content_type": "json",
                "secret": "G9KNgSeNb1xkhXFe6ZgnIJkUptGJZ2",
                "url": "https://apps.fedoraproject.org/github2fedmsg/webhook"
            },
            "created_at": "2014-06-18T21:32:43Z",
            "events": [ "*" ],
            "id": 2442140,
            "last_response": {
                "code": None,
                "message": None,
                "status": "unused"
            },
            "name": "web",
            "updated_at": "2014-06-18T21:32:43Z",
            "url": "https://api.github.com/repos/ralphbean/apps.fp.o/"
            "hooks/2442140",
        },
        "hook_id": 2442140,
        "zen": "Keep it logically awesome."
    },
    "msg_id": "2014-6552feeb-6dd9-4c39-9839-2c35f0a0f498",
    "source_name": "datanommer",
    "source_version": "0.6.4",
    "timestamp": 1403127164.0,
    "topic": "org.fedoraproject.prod.github.webhook",
    "crypto": "x509",
}
}

umb_message = {
"headers": {
    "content-length": "598",
    "expires": "0",
    "old": "OPEN",
    "JMS_AMQP_MESSAGE_FORMAT": "0",
    "parent": "null",
    "JMS_AMQP_NATIVE": "false",
    "destination": "/topic/VirtualTopic.eng.brew.task.closed",
    "method": "newRepo",
    "priority": "4",
    "message-id": "ID\\cmessaging-devops-broker01.web.prod.ext.phx2.redhat.com-32888-1493960489068-4\\c473057\\c0\\c0\\c1",
    "timestamp": "0",
    "attribute": "state",
    "new": "CLOSED",
    "JMS_AMQP_FirstAcquirer": "false",
    "type": "TaskStateChange",
    "id": "13317101",
    "subscription": "/queue/Consumer.datanommer-dev-mikeb.VirtualTopic.eng.>"
},
"body": {
    "username": None,
    "source_name": "datanommer",
    "certificate": None,
    "i": 0,
    "timestamp": 1496253497.0,
    "msg_id": "ID\\cmessaging-devops-broker01.web.prod.ext.phx2.redhat.com-"
    "32888-1493960489068-4\\c473057\\c0\\c0\\c1",
    "crypto": None,
    "topic": "/topic/VirtualTopic.eng.brew.task.closed",
    "signature": None,
    "source_version": "0.7.0",
    "msg": {
        "info": {
            "weight": 0.1,
            "parent": None,
            "completion_time": "2017-05-31 17:58:20.299696",
            "start_ts": 1496253256.59157,
            "start_time": "2017-05-31 17:54:16.591569",
            "request": [
                "rhos-12.0-rhel-7-build"
            ],
            "waiting": False,
            "awaited": None,
            "label": None,
            "priority": 15,
            "channel_id": 3,
            "state": 2,
            "create_time": "2017-05-31 17:54:15.915999",
            "create_ts": 1496253255.916,
            "owner": 3371,
            "host_id": 93,
            "method": "newRepo",
            "completion_ts": 1496253500.2997,
            "arch": "noarch",
            "id": 13317101,
            "result": [
                2041311,
                15755194
            ]
        },
        "attribute": "state",
        "old": "OPEN",
        "new": "CLOSED"
    }
}}


class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import fedmsg.config
        import fedmsg.meta

        config = fedmsg.config.load_config([], None)

        if USE_SQLITE:
            fname = "sqlite:///%s" % filename
        else:
            response = requests.get('http://faitout.fedorainfracloud.org/new',
                                    headers=dict(accept='application/json'))
            details = response.json()
            fname = "postgres://{username}:{password}@{host}:{port}/{dbname}"\
                .format(**details)
            cls.dbname = details['dbname']

        config['datanommer.sqlalchemy.url'] = cls.fname = fname
        fedmsg.meta.make_processors(**config)

    @classmethod
    def tearDownClass(cls):
        if not USE_SQLITE:
            requests.get('http://faitout.fedorainfracloud.org/drop/{dbname}'\
                         .format(dbname=cls.dbname))

    def setUp(self):
        if not USE_SQLITE:
            response = requests.get('http://faitout.fedorainfracloud.org/clean/{dbname}'.\
                                    format(dbname=self.dbname))
        # We only have to do this so that we can do it over
        # and over again for each test.
        datanommer.models.session = scoped_session(datanommer.models.maker)
        datanommer.models.init(self.fname, create=True)


    def tearDown(self):
        if USE_SQLITE:
            engine = datanommer.models.session.get_bind()
            datanommer.models.DeclarativeBase.metadata.drop_all(engine)
        datanommer.models.session.close()

        # These contain objects bound to the old session, so we have to flush.
        datanommer.models._users_seen = set()
        datanommer.models._packages_seen = set()

    @raises(KeyError)
    def test_add_empty(self):
        datanommer.models.add(dict())

    def test_add_missing_i(self):
        msg = copy.deepcopy(scm_message)
        del msg['body']['i']
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        self.assertEqual(dbmsg.i, 0)

    def test_add_missing_timestamp(self):
        msg = copy.deepcopy(scm_message)
        del msg['body']['timestamp']
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        timediff = datetime.datetime.now() - dbmsg.timestamp
        # 10 seconds between adding the message and checking
        # the timestamp should be more than enough.
        self.assertTrue(timediff < datetime.timedelta(seconds=10))

    def test_add_missing_msg_id_with_timestamp(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        self.assertTrue(dbmsg.msg_id.startswith('2012-'))

    def test_add_missing_msg_id_no_timestamp(self):
        msg = copy.deepcopy(scm_message)
        del msg['body']['timestamp']
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        year = datetime.datetime.now().year
        self.assertTrue(dbmsg.msg_id.startswith(unicode(year) + u'-'))

    def test_extract_base_username(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        self.assertEquals(dbmsg.__json__()['username'], msg['body']['username'])
        self.assertEquals(dbmsg.__json__()['crypto'], None)

    def test_extract_crypto_type(self):
        msg = copy.deepcopy(github_message)
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        self.assertEquals(dbmsg.__json__()['username'], None)
        self.assertEquals(dbmsg.__json__()['crypto'], 'x509')

    def test_add_many_and_count_statements(self):
        statements = []

        def track(conn, cursor, statement, param, ctx, many):
            statements.append(statement)

        engine = datanommer.models.session.get_bind()
        sqlalchemy.event.listen(engine, "before_cursor_execute", track)

        msg = copy.deepcopy(scm_message)

        # Add it to the db and check how many queries we made
        datanommer.models.add(msg)
        eq_(len(statements), 7)

        # Add it again and check again
        datanommer.models.add(msg)
        pprint.pprint(statements)
        eq_(len(statements), 10)

    def test_add_missing_cert(self):
        msg = copy.deepcopy(scm_message)
        del msg['body']['certificate']
        datanommer.models.add(msg)

    def test_add_and_check_for_others(self):
        # There are no users or packages at the start
        eq_(datanommer.models.User.query.count(), 0)
        eq_(datanommer.models.Package.query.count(), 0)

        # Then add a message
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)

        # There should now be one of each
        eq_(datanommer.models.User.query.count(), 1)
        eq_(datanommer.models.Package.query.count(), 1)

        # If we add it again, there should be no duplicates
        msg['body']['msg']['msg_id'] = 'foobar2'
        datanommer.models.add(msg)
        eq_(datanommer.models.User.query.count(), 1)
        eq_(datanommer.models.Package.query.count(), 1)

        msg = copy.deepcopy(scm_message)
        msg['body']['msg']['commit']['username'] = 'ralph'
        msg['body']['msg']['msg_id'] = 'foobar3'
        datanommer.models.add(msg)
        eq_(datanommer.models.User.query.count(), 2)
        eq_(datanommer.models.Package.query.count(), 1)

    def test_add_nothing(self):
        eq_(datanommer.models.Message.query.count(), 0)

    def test_add_and_check(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        eq_(datanommer.models.Message.query.count(), 1)

    def test_categories(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        obj = datanommer.models.Message.query.first()
        eq_(obj.category, 'git')

    def test_categories_with_umb(self):
        msg = copy.deepcopy(umb_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        obj = datanommer.models.Message.query.first()
        eq_(obj.category, 'brew')

    def test_grep_all(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        t, p, r = datanommer.models.Message.grep()
        eq_(t, 1)
        eq_(p, 1)
        eq_(len(r), 1)
        eq_(r[0].msg, scm_message['body']['msg'])

    def test_grep_category(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        t, p, r = datanommer.models.Message.grep(categories=['git'])
        eq_(t, 1)
        eq_(p, 1)
        eq_(len(r), 1)
        eq_(r[0].msg, scm_message['body']['msg'])

    def test_grep_not_category(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        t, p, r = datanommer.models.Message.grep(not_categories=['git'])
        eq_(t, 0)
        eq_(p, 0)
        eq_(len(r), 0)

    def test_add_with_close_category(self):
        msg = copy.deepcopy(github_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        t, p, r = datanommer.models.Message.grep(categories=['github'])
        eq_(t, 1)
        eq_(p, 1)
        eq_(len(r), 1)
        eq_(r[0].msg_id, '2014-6552feeb-6dd9-4c39-9839-2c35f0a0f498')

    def test_timezone_awareness(self):
        msg = copy.deepcopy(github_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()

        queried = datanommer.models.Message.query.one()

        t = queried.timestamp
        eq_(t, datetime.datetime(2014, 6, 18, 21, 32, 44))

    def test_add_no_headers(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        self.assertEquals(dbmsg.headers, {})

    def test_add_headers(self):
        msg = copy.deepcopy(scm_message)
        msg['headers'] = {'foo': 'bar', 'baz': 1, 'wibble': ['zork', 'zap']}
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        self.assertEquals(dbmsg.headers, msg['headers'])

    def test_add_headers_message_id(self):
        msg = copy.deepcopy(scm_message)
        msg['headers'] = {'message-id': 'abc123'}
        datanommer.models.add(msg)
        dbmsg = datanommer.models.Message.query.first()
        self.assertEquals(dbmsg.msg_id, 'abc123')

    def test_add_duplicate(self):
        # use the github message because it has a msg_id
        msg = copy.deepcopy(github_message)
        datanommer.models.add(msg)
        datanommer.models.add(msg)
        # if no exception was thrown, then we successfully ignored the
        # duplicate message
        eq_(datanommer.models.Message.query.count(), 1)

    def test_User_get_or_create(self):
        eq_(datanommer.models.User.query.count(), 0)
        datanommer.models.User.get_or_create(u'foo')
        eq_(datanommer.models.User.query.count(), 1)
        datanommer.models.User.get_or_create(u'foo')
        eq_(datanommer.models.User.query.count(), 1)

    def test_Package_get_or_create(self):
        eq_(datanommer.models.Package.query.count(), 0)
        datanommer.models.Package.get_or_create(u'foo')
        eq_(datanommer.models.Package.query.count(), 1)
        datanommer.models.Package.get_or_create(u'foo')
        eq_(datanommer.models.Package.query.count(), 1)
