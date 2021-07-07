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
# Ridiculous as it may seem, we need to import multiprocessing and
# logging here in order to get tests to pass smoothly on python 2.7.
try:
    import logging
    import multiprocessing
except Exception:
    pass

import sys

from setuptools import setup


f = open("README.rst")
long_description = f.read().strip()
long_description = long_description.split("split here", 1)[-1]
f.close()

version = "0.3.0"

setup(
    name="datanommer",
    version=version,
    description="A storage consumer for the Fedora Message Bus (fedmsg)",
    long_description=long_description,
    author="Ralph Bean",
    author_email="rbean@redhat.com",
    url="http://github.com/fedora-infra/datanommer",
    license="GPLv3+",
    install_requires=[
        "datanommer.consumer",
        "datanommer.models",
        "datanommer.commands",
    ],
)
