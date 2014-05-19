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
from setuptools import setup, find_packages
import sys

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[1]
f.close()

version = '0.4.6'

setup(
    name='datanommer.commands',
    version=version,
    description="Console comands for datanommer",
    long_description=long_description,
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='http://github.com/fedora-infra/datanommer',
    license='GPLv3+',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['datanommer'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "datanommer.models",
        "fedmsg",
    ],
    entry_points={
        'console_scripts': (
            'datanommer-create-db=datanommer.commands:create',
            'datanommer-dump=datanommer.commands:dump',
            'datanommer-stats=datanommer.commands:stats',
            'datanommer-latest=datanommer.commands:latest',
        ),
    },
    tests_require=[
        "nose",
        "mock",
        "fedmsg_meta_fedora_infrastructure",
    ],
    test_suite='nose.collector',
)
