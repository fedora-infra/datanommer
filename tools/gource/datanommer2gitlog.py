#!/usr/bin/env python

# This file is a part of datanommer, a message sink for fedmsg.
# Copyright (C) 2014, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
""" datanommer2gitlog.py -- Read in datanommer's entire db...
...write out a corresponding fake git history.

Run with python3.

    $ cd ~
    $ rm -rf myrepo
    $ mkdir myrepo
    $ cd myrepo
    $ git init
    $ python ../datanommer2gitlog.py

"""

import json
import os
import subprocess

import fedmsg.config
import fedmsg.text
import progressbar


def run(cmd):
    """Execute a shell command.

    Both envoy and python-sh failed me...
    commands, although deprecated, feels like the easiest tool to use.
    """

    result = subprocess.run(cmd, text=True, stderr=subprocess.STDOUT)
    if result.returncode:
        print(result.stdout)
    return result.returncode == 0


def read_datanommer_entries_from_filedump():
    """Read in all datanommer entries from a file created with:

    $ datanommer-dump > myfile.json
    """

    # TODO -- un-hardcode this filename when I need to run this next time.
    # filename = "../myfile.json"
    filename = "../datanommer-dump-2012-11-22.json"
    print("Reading %s" % filename)
    progress = progressbar.ProgressBar(
        widgets=[
            progressbar.widgets.Percentage(),
            progressbar.widgets.Bar(),
            progressbar.widgets.ETA(),
        ]
    )

    def _entries():
        failed = 0
        with open(filename) as f:
            raw = f.read()
            lines = raw.split("\n}\n")
            for line in progress(lines):
                try:
                    yield json.loads(line + "\n}")
                except Exception:
                    failed += 1
        print(" * Failed to parse %i json objects" % failed)

    def comp(a, b):
        return (a["timestamp"] > b["timestamp"]) - (a["timestamp"] < b["timestamp"])

    result = sorted(list(_entries()), cmp=comp)
    print(" * Read and sorted %i messages" % len(result))
    print()
    return result


def main():
    progress = progressbar.ProgressBar(
        widgets=[
            progressbar.widgets.Percentage(),
            progressbar.widgets.Bar(),
            progressbar.widgets.ETA(),
        ]
    )
    conf = fedmsg.config.load_config(None, [])
    fedmsg.text.make_processors(**conf)

    # Check that this actually is a git repo before doing anything.
    if not run(["git", "status"]):
        raise OSError("Not a git repository.")

    failed_adds, failed_commits = 0, 0

    entries = read_datanommer_entries_from_filedump()
    print("Writing out fake git log.")
    for i, entry in enumerate(progress(entries)):
        original_msg = entry  # Do this when reading from the json dump

        processor = fedmsg.text.msg2processor(entry)
        modname = processor.__name__.lower()  # one of "Bodhi", "FAS", "Wiki".. etc.
        conf["processor"] = processor
        conf["legacy"] = True

        try:
            text = fedmsg.text.msg2repr(original_msg, **conf)
            text = text.encode("utf-8")

            if not text:
                text = "..empty.."

            text = text.replace('"', "")

        except IndexError:
            print(" * failed at applying msg2repr to obj")
            continue

        users = fedmsg.text.msg2usernames(original_msg, **conf)
        objs = fedmsg.text.msg2objects(original_msg, **conf)

        # Some messages just aren't associated with a user
        if not users:
            user = "root"
        else:
            user = users.pop()

        # Some messages just aren't associated with an object
        if not objs:
            filenames = [modname + "/default"]
        else:
            filenames = [modname + "/" + o for o in objs]

        for filename in filenames:

            # clean the filename
            for cha in " ()!;|&*?`":
                filename = filename.replace(cha, "")

            parent = filename.rsplit("/", 1)[0]
            if not os.path.isdir(parent):
                os.makedirs(parent)

            with open(filename, "a") as f:
                f.write(text + "\n")

            if not run(["git", "add", filename]):
                failed_adds += 1
                print(" * Failed the %ith add." % failed_adds)

        # It's annoying that you can't override the commit date more directly.
        # Using git commit --date=foo only sets the author date.
        os.environ["GIT_AUTHOR_DATE"] = "%i+0000" % entry["timestamp"]
        os.environ["GIT_COMMITTER_DATE"] = "%i+0000" % entry["timestamp"]
        try:
            cmd = [
                "git",
                "commit",
                "--message",
                text,
                "--author",
                f"{user} <{user}@fedoraproject.org>",
            ]
        except UnicodeDecodeError:
            print(" * unicode failure on %s" % text)
            failed_commits += 1
            continue

        if not run(cmd):
            failed_commits += 1
            print(" * Failed the %ith commit." % failed_commits)
            print(cmd)

    print("Done.  %i failed adds, %i failed commits." % (failed_adds, failed_commits))


if __name__ == "__main__":
    main()
