#!/bin/bash -e

echo "Running tests for all packages"
for package in datanommer.{models,consumer,commands}; do
    echo "[$package] Testing..."
    pushd $package
    python setup.py test
    popd
    echo "[$package] done."
done
