#!/usr/bin/env python

import os
from collections import defaultdict

import toml


SUBPROJECTS = ["commands", "consumer", "models"]
SUPPORTED_LOCK_VERSION = "1.1"


deps_by_package = defaultdict(dict)

for project in SUBPROJECTS:
    lock_path = os.path.join(f"datanommer.{project}", "poetry.lock")
    with open(lock_path) as f:
        lockfile = toml.load(f)
    lock_version = lockfile["metadata"]["lock-version"]
    if lock_version != SUPPORTED_LOCK_VERSION:
        print(f"Unsupported lockfile version in {lock_path}: {lock_version}. Skipping.")
        continue
    deps = {}
    for dep in lockfile["package"]:
        deps_by_package[dep["name"]][project] = dep["version"]


for name, deps in deps_by_package.items():
    if len(set(deps.values())) == 1:
        continue
    dep_list = [f"{project}:{version}" for project, version in deps.items()]
    print(f"Incoherent dep for {name}: {' '.join(dep_list)}")
