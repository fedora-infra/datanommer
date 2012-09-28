from setuptools import setup, find_packages
import sys
import os

import multiprocessing
import logging

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[1]
f.close()

version = '0.1.7'

setup(name='datanommer',
      version=version,
      description="A storage consumer for the Fedora Message Bus (fedmsg)",
      long_description=long_description,
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords='',
      author='Ralph Bean',
      author_email='rbean@redhat.com',
      url='http://github.com/ralphbean/datanommer',
      license='GPLv3+',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "moksha.hub>=1.0.3",
          "fedmsg>=0.5.0",
          "sqlalchemy>=0.7",
      ],
      tests_require=[
          "nose",
      ],
      test_suite='nose.collector',
      entry_points={
          'console_scripts': (
              'datanommer-create-db=datanommer.commands:create',
              'datanommer-dump=datanommer.commands:dump',
              'datanommer-stats=datanommer.commands:stats',
          ),
          'moksha.consumer': (
              'noms = datanommer.consumer:Nommer'
          ),
      }
)
