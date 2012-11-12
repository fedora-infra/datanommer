from setuptools import setup, find_packages
import sys

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[1]
f.close()

version = '0.2.0'

setup(
    name='datanommer.consumer',
    version=version,
    description="Hub consumer plugin for datanommer",
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
        "datanommer.models",
        "fedmsg",
    ],
    entry_points={
        'moksha.consumer': (
            'noms = datanommer.consumer:Nommer'
        ),

    },
)
