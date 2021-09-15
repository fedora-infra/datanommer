# datanommer

This is datanommer. It is comprised of only a [fedmsg][] consumer that
stuffs every message in a sqlalchemy database.

There are also a handful of CLI tools to dump information from the
database.

## Build Status

| Branch  | Status                                  |
|---------|-----------------------------------------|
| master  | [![Build Status - master branch][]][1]  |
| develop | [![Build Status - develop branch][]][1] |

# Try it out

## Using a virtualenv

Using a virtual environment is highly recommended, although this is not
a must. Using virtualenvwrapper can isolate your development
environment. You will be able to work on the latest datanommer from git
checkout without messing the installed datanommer copy in your system.

Install virtualenvwrapper by:

    $ sudo yum install python-virtualenvwrapper

**Note:** If you decide not to use python-virtualenvwrapper, you can
always use latest update of fedmsg and datanommer in fedora. If you are
doing this, simply ignore all mkvirtualenv and workon commands in these
instructions. You can install fedmsg with `sudo yum install fedmsg`, and
datanommer with `sudo yum install datanommer`.

## Development dependencies

Get:

    $ sudo yum install python-virtualenv openssl-devel zeromq-devel gcc

**Note:** If submitting patches, you should check [Contributing][] for
style guidelines.

## Set up virtualenv

Create a new, empty virtualenv and install all the dependencies from
pypi:

    $ mkvirtualenv datanommer
    (datanommer)$ cdvirtualenv

**Note:** If the mkvirtualenv command is unavailable try
`source /usr/bin/virtualenvwrapper.sh` on Fedora (if you do not run
Fedora you might have to adjust the command a little). You can also add
this command to your `~/.bashrc` file to have it run automatically for
you.

## Cloning upstream the git repo

The source code is on github.

Get fedmsg:

    (datanommer)$ git clone https://github.com/fedora-infra/fedmsg.git

Get datanommer:

    (datanommer)$ git clone https://github.com/fedora-infra/datanommer.git

Set up fedmsg:

    (datanommer)$ cd fedmsg

For development, avoid editing master branch. Checkout develop branch:

    (datanommer)$ git checkout develop
    (d

  [fedmsg]: http://github.com/fedora-infra/fedmsg
  [Build Status - master branch]: https://img.shields.io/travis/fedora-infra/datanommer/master.svg
  [1]: https://travis-ci.org/fedora-infra/datanommer/branches
  [Build Status - develop branch]: https://img.shields.io/travis/fedora-infra/datanommer/develop.svg
  [Contributing]: https://fedmsg.readthedocs.io/en/stable/contributing/
