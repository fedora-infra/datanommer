#!/usr/bin/env python

import datanommer.models
import fedmsg.encoding

if __name__ == '__main__':
    datanommer.models.init("sqlite:///datanommer.db")

    for model in datanommer.models.models:
        for entry in model.query.all():
            print fedmsg.encoding.pretty_dumps(entry)
