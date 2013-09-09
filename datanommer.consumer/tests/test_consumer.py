import unittest
import mock
import copy

from nose.tools import eq_

import datanommer.consumer
import datanommer.models

import os

filename = "datanommer-test.db"


class TestConsumer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import fedmsg.config
        import fedmsg.meta

        config = fedmsg.config.load_config([], None)
        uri = "sqlite:///%s" % filename
        config['datanommer.sqlalchemy.url'] = uri
        fedmsg.meta.make_processors(**config)
        cls.fedmsg_config = config

    def setUp(self):
        class FakeHub(object):
            config = self.fedmsg_config

            def subscribe(*args, **kwargs):
                pass

        datanommer.models.init(
            self.fedmsg_config['datanommer.sqlalchemy.url'],
            create=True,
        )
        datanommer.consumer.Nommer._initialized = True  # Clearly, a lie.
        self.consumer = datanommer.consumer.Nommer(FakeHub())

    def tearDown(self):
        os.remove(filename)

    def test_duplicate_msg_id(self):
        example_message = dict(
            topic="topiclol",
            body=dict(
                topic="topiclol",
                i=1,
                msg_id="1234",
                timestamp=1234,
                msg=dict(
                    foo="bar",
                )
            )
        )
        msg1 = copy.deepcopy(example_message)
        msg2 = copy.deepcopy(example_message)

        self.consumer.consume(msg1)
        eq_(datanommer.models.Message.query.count(), 1)

        with mock.patch("fedmsg.publish") as mocked_function:
            self.consumer.consume(msg2)
            eq_(datanommer.models.Message.query.count(), 2)

        mocked_function.assert_called_once()
