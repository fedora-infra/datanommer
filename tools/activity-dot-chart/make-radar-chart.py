import calendar
from datetime import (
    datetime,
    timedelta,
)
import fedmsg.config
import fedmsg.meta
import pygal

from sqlalchemy.orm.exc import NoResultFound
import datanommer.models as m
m.init('postgres://datanommer:bunbunbun@localhost/datanommer')

title_template = 'Fedora Development Activity for %s@fedoraproject.org'


def message_count(user, category):
    return len([
        msg for msg in user.messages
        if msg.category == category
    ])


def make_chart(username):
    # TODO -- replace print with logging
    print "Building chart for %r" % username
    chart = pygal.Radar(logarithmic=True, fill=True)
    chart.title = title_template % username

    try:
        user = m.User.query.filter(m.User.name == username).one()
    except NoResultFound:
        user = None

    config = fedmsg.config.load_config()
    fedmsg.meta.make_processors(**config)
    categories = [p.__name__.lower() for p in fedmsg.meta.processors]

    excluded = ['logger', 'announce', 'compose', 'unhandled']
    for item in excluded:
        categories.remove(item)

    data = [message_count(user, category) for category in categories]
    chart.x_labels = categories

    # Remove 'zero' valued categories.
    #chart.x_labels = [c for i, c in enumerate(categories) if data[i]]
    #data = [item for item in data if item]

    chart.add(username, data)

    return chart


def main():
    # TODO -- use argparse
    username = 'ralph'

    chart = make_chart(username)

    # TODO - use argparse
    chart.render_to_file('pygal-chart-%s.svg' % username)


if __name__ == '__main__':
    main()
