#!/bin/bash -e

echo "Installing all packages in development mode"
for package in datanommer.{models,consumer,commands}; do
    echo "[$package] Testing..."
    pushd $package
    python setup.py test
    popd
    echo "[$package] done."
done
