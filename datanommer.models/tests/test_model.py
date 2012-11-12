import copy
import os
import sqlalchemy.exc
import unittest

from nose.tools import raises
from nose.tools import eq_

import datanommer.models

filename = "datanommer-test.db"

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
        }
    },
    "signature": "blah",
    "certificate": "blah",
}


class TestModels(unittest.TestCase):
    def setUp(self):
        datanommer.models.init("sqlite:///%s" % filename, create=True)

    def tearDown(self):
        os.remove(filename)

    @raises(KeyError)
    def test_add_empty(self):
        datanommer.models.add(dict())

    @raises(KeyError)
    def test_add_missing_i(self):
        msg = copy.deepcopy(scm_message)
        del msg['i']
        datanommer.models.add(msg)

    def test_add_missing_cert(self):
        msg = copy.deepcopy(scm_message)
        del msg['certificate']
        datanommer.models.add(msg)

    def test_add_nothing(self):
        eq_(datanommer.models.GitMessage.query.count(), 0)

    def test_add_and_check(self):
        msg = copy.deepcopy(scm_message)
        datanommer.models.add(msg)
        datanommer.models.session.flush()
        eq_(datanommer.models.GitMessage.query.count(), 1)
