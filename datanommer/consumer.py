
import fedmsg.consumers
import pymongo

DEFAULTS = {
    'enabled': True,  # TODO - Set this to False someday
    'mongo.host': 'localhost',
    'mongo.port': 27017,
    'mongo.db': 'fedmsg',
}


import logging
log = logging.getLogger("fedmsg")


class Nommer(fedmsg.consumers.FedmsgConsumer):
    topic = "*"

    def __init__(self, hub):
        # Grab the config specified in /etc/fedmsg.d/datanommer.py
        self.config = hub.config.get('datanommer', DEFAULTS)

        if not self.config['enabled']:
            log.info("DataNommer disabled by config.")
            return

        super(Nommer, self).__init__(hub)

        # Setup a mongo db connection.
        self.connection = pymongo.Connection(
            self.config['mongo.host'], self.config['mongo.port'])
        self.db = self.connection[self.config['mongo.db']]
        self.collection = self.db.messages

    def consume(self, message):
        log.debug("Nomming %r" % message)
        self.collection.insert(message)
