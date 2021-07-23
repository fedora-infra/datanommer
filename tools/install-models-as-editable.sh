#!/bin/sh

# Install datanommer.models in develop mode when run from a virtualenv such as
# those tox creates.

set -e
set -x

pushd ../datanommer.models
poetry install
popd
