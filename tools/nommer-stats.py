#!/usr/bin/env python

import datanommer.models


if __name__ == '__main__':
    datanommer.models.init("sqlite:///datanommer.db")

    for model in datanommer.models.models:
        print model, "has", model.query.count(), "entries"
