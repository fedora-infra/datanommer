from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='datanommer',
      version=version,
      description="Store all the messages on the fedmsg bus, ever.",
      long_description="""\
""",
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
          "fedmsg>=0.2.2",
          "pymongo",
      ],
      entry_points={
          'moksha.consumer': (
              'noms = datanommer.consumer:Nommer'
          ),
      }
)
