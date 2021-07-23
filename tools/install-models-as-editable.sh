#!/bin/sh

# Install datanommer.models in develop mode when run from a virtualenv such as
# those tox creates.

set -e
set -x

CURDIR=`pwd`
cd ../datanommer.models
"$CURDIR"/.tox/.tox/bin/poetry install
cd "$CURDIR"
