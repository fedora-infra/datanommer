from setuptools import setup, find_packages
import sys

import multiprocessing
import logging

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[1]
f.close()

version = '0.2.0'

setup(name='datanommer.models',
      version=version,
      description="SQLAlchemy models for datanommer",
      long_description=long_description,
      author='Ralph Bean',
      author_email='rbean@redhat.com',
      url='http://github.com/ralphbean/datanommer',
      license='GPLv3+',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      namespace_packages=['datanommer'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "sqlalchemy>=0.7",
          "fedmsg",
      ],
      tests_require=[
          "nose",
      ],
      test_suite='nose.collector',
)
