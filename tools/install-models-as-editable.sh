#!/bin/sh

# Install datanommer.models in develop mode when run from a virtualenv such as
# those tox creates.

set -e

CURDIR=`pwd`

set -x

cd ../datanommer.models
poetry install --all-extras
cd "$CURDIR"
