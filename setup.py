from setuptools import setup, find_packages
import sys

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[-1]
f.close()

version = '0.2.0'

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
)
