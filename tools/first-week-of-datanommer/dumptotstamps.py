#!/usr/bin/env python

with open("datanommer-dump-2012-10-16.json", "r") as f:
    lines = f.readlines()

lines = [l.strip() for l in lines if l.startswith("  \"timestamp")]
values = [float(l.split(":")[-1][:-1].strip()) for l in lines]
for value in values:
    print value

