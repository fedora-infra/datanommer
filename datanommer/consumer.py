import fedmsg.consumers
import datanommer.models

DEFAULTS = {
    'datanommer.enabled': True,
    'datanommer.sqlalchemy.url': 'sqlite:///datanommer.db',
}


import logging
log = logging.getLogger("fedmsg")


class Nommer(fedmsg.consumers.FedmsgConsumer):
    topic = "*"
    config_key = 'datanommer.enabled'

    def __init__(self, hub):
        super(Nommer, self).__init__(hub)

        # If fedmsg doesn't think we should be enabled, then we should quit
        # before setting up all the extra special zmq machinery.
        # __initialized is set in moksha.api.hub.consumer
        if not getattr(self, "__initialized", False):
            return

        # Setup a sqlalchemy DB connection (postgres, or sqlite)
        datanommer.models.init(self.hub.config['datanommer.sqlalchemy.url'])

    def consume(self, message):
        log.debug("Nomming %r" % message)
        datanommer.models.add(message['body'])
