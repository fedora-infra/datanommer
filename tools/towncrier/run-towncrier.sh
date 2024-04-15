#!/bin/bash

set -e

echo "Building release notes for all packages"
for package in datanommer.{models,consumer,commands}; do
    echo "[$package] Building release notes..."
    pushd $package
    poetry install --all-extras
    poetry run towncrier build --yes $@
    popd
    echo "[$package] done."
done
