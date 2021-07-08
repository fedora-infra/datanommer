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


with open("datanommer-dump-2012-10-16.json") as f:
    lines = f.readlines()

lines = [line.strip() for line in lines if line.startswith('  "timestamp')]
values = [float(line.split(":")[-1][:-1].strip()) for line in lines]
for value in values:
    print(value)
