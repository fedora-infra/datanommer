#!/usr/bin/env python
""" Print a list of the contributors whose names have appeared in any event
in the last 60 days.

https://fedorahosted.org/fesco/ticket/967#comment:2

:Author:  Ralph Bean <rbean@redhat.com>
"""


__requires__ = 'datanommer==0.1.8'
import sys
from pkg_resources import load_entry_point

import datanommer.models as m
import fedmsg.config
import fedora.accounts.fas2

import datetime
import getpass
import pprint


def prompt_creds():
    print "I need to query FAS to get the list of packagers.."
    username = raw_input("FAS username: ")
    password = getpass.getpass("FAS password: ")
    return dict(username=username, password=password)


def get_packagers():
    options = dict(cache_session=True)
    options.update(prompt_creds())
    s = fedora.accounts.fas2.AccountSystem(**options)
    packagers = s.people_by_groupname("packager")
    return packagers


def init():
    # Load stuff from /etc/fedmsg.d/ into a dict
    config = fedmsg.config.load_config(None, [])

    m.init(config['datanommer.sqlalchemy.url'])


def handle_bodhi(msg):
    """ Given a bodhi message, return the FAS username. """

    if 'bodhi.update.comment' in msg.topic:
        username = msg.msg['comment']['author']
    elif 'bodhi.buildroot_override' in msg.topic:
        username = msg.msg['override']['submitter']
    else:
        username = msg.msg.get('update', {}).get('submitter')
    return username


def handle_wiki(msg):
    """ Given a wiki message, return the FAS username. """

    if 'wiki.article.edit' in msg.topic:
        username = msg.msg['user']
    elif 'wiki.upload.complete' in msg.topic:
        username = msg.msg['user_text']
    else:
        raise ValueError("Unhandled topic.")

    return username


def handle_fas(msg):
    """ Given a FAS message, return the FAS username. """

    return msg.msg['agent']['username']

# This is a mapping of datanommer models to functions that can extract the
# username from a message of that model type.
username_extractors = {
    m.BodhiMessage: handle_bodhi,
    m.WikiMessage: handle_wiki,
    m.FASMessage: handle_fas,
    #m.GitMessage: handle_git,
}

if __name__ == '__main__':
    init()

    # Get the full list of people in the packagers group from FAS.
    packagers = get_packagers()

    # A list of FAS usernames we're going to build from fedmsg messages.
    seen = set()

    # TODO -- have this configurable with a switch.  60 days or 90 days.
    then = datetime.datetime.now() - datetime.timedelta(days=60)

    for model, extractor in username_extractors.items():
        query = model.query
        query = query.filter(model.timestamp > then)

        for msg in query.all():
            seen.add(extractor(msg))

    for packager in packagers:
        if packager['username'] in seen or packager['email'] in seen:
            packagers_seen.append(packager['username'])

    print len(seen), "persons seen in total"
    print len(packagers_seen), "of", len(packagers), "seen"

