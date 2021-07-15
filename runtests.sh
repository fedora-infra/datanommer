#!/bin/bash

set -e

which tox &>/dev/null || {
    echo "You need to install tox" >&2
    exit 2
}
which pre-commit &>/dev/null || {
    echo "You need to install pre-commit" >&2
    exit 2
}
which krb5-config &> /dev/null || {
    echo "You need to install krb5-devel" >&2
    exit 2
}

echo "Running checks for all packages"
pre-commit run --all-files

echo "Running unit tests for all packages"
for package in datanommer.{models,consumer,commands}; do
    echo "[$package] Testing..."
    pushd $package
    tox $@
    popd
    echo "[$package] done."
done
