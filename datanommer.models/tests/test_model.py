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
import os
import sqlalchemy.exc
import unittest

from sqlalchemy.orm import scoped_session

from nose.tools import raises
from nose.tools import eq_

import datanommer.models


filename = ":memory:"

scm_message = {
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
}


class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import fedmsg.config
        import fedmsg.meta

        config = fedmsg.config.load_config([], None)
        fname = "sqlite:///%s" % filename
        config['datanommer.sqlalchemy.url'] = fname
        fedmsg.meta.make_processors(**config)

    def setUp(self):
        fname = "sqlite:///%s" % filename
        # We only have to do this so that we can do it over
        # and over again for each test.
        datanommer.models.session = scoped_session(datanommer.models.maker)
        datanommer.models.init(fname, create=True)

    def tearDown(self):
        engine = datanommer.models.session.get_bind()
        datanommer.models.DeclarativeBase.metadata.drop_all(engine)

    @raises(KeyError)
    def test_add_empty(self):
        datanommer.models.add(dict())

    @raises(KeyError)
    def test_add_missing_i(self):
        msg = copy.deepcopy(scm_message)
        del msg['i']
        datanommer.models.add(msg)

    @raises(KeyError)
    def test_add_missing_timestamp(self):
        msg = copy.deepcopy(scm_message)
        del msg['timestamp']
        datanommer.models.add(msg)

    def test_add_missing_cert(self):
        msg = copy.deepcopy(scm_message)
        del msg['certificate']
        datanommer.models.add(msg)

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

    def test_grep_all(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        t, p, r = datanommer.models.Message.grep()
        eq_(t, 1)
        eq_(p, 1)
        eq_(len(r), 1)
        eq_(r[0].msg, scm_message['msg'])

    def test_grep_category(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        t, p, r = datanommer.models.Message.grep(categories=['git'])
        eq_(t, 1)
        eq_(p, 1)
        eq_(len(r), 1)
        eq_(r[0].msg, scm_message['msg'])

    def test_grep_not_category(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        t, p, r = datanommer.models.Message.grep(not_categories=['git'])
        eq_(t, 0)
        eq_(p, 0)
        eq_(len(r), 0)
