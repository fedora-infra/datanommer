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
import importlib.metadata
import logging

from fedora_messaging import config

import datanommer.models as m


__version__ = importlib.metadata.version("datanommer-consumer")


def get_datanommer_sqlalchemy_url():
    try:
        return config.conf["consumer_config"]["datanommer_sqlalchemy_url"]
    except KeyError as e:
        raise ValueError(
            "datanommer_sqlalchemy_url not defined in the fedora-messaging config"
        ) from e


log = logging.getLogger("datanommer-consumer")


class Nommer:
    def __init__(self):
        m.init(get_datanommer_sqlalchemy_url())

    def __call__(self, message):
        log.info("Nomming %r", message)
        try:
            m.add(message)
        except Exception:
            m.session.rollback()
            raise
