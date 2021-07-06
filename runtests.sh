#!/bin/bash

set -e

echo "Running tests for all packages"
for package in datanommer.{models,consumer,commands}; do
    echo "[$package] Testing..."
    pushd $package
    tox $@
    popd
    echo "[$package] done."
done
