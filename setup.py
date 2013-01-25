# Ridiculous as it may seem, we need to import multiprocessing and
# logging here in order to get tests to pass smoothly on python 2.7.
try:
    import multiprocessing
    import logging
except Exception:
    pass

from setuptools import setup
import sys


tests_require = [
    'nose'
    , 'mock'
]

if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
    tests_require.extend([
        'unittest2',
    ])

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[-1]
f.close()

version = '0.3.0'

setup(name='datanommer',
      version=version,
      description="A storage consumer for the Fedora Message Bus (fedmsg)",
      long_description=long_description,
      author='Ralph Bean',
      author_email='rbean@redhat.com',
      url='http://github.com/ralphbean/datanommer',
      license='GPLv3+',
      install_requires=[
          "datanommer.consumer",
          "datanommer.models",
          "datanommer.commands",
      ],
      tests_require=tests_require,
      test_suite='nose.collector'
)
