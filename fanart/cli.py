"""Fanart CLI script

Usage:
  fanart [options]

Boring options:
  -h, --help                Show this screen

Backend options:
  --config CONFIG_FILE      Configuration file to use
  --db-url SQLA_URL         The database URL, in SQLAlchemy format
  --scratch SCRATCH_DIR     Scratch directory

    Default connection info is read from the given CONFIG_FILE, or file
    named by an environment variable called FANART_CONFIG_FILE, or
    a file called 'cli.ini' or 'development.ini', in that order.

Login options:
  --guest                   Be a guest
  -u USER, --user USER      Be the specified user

    By default, an omniscient, all-powerful admin is assumed.

Debug options:
  -d --debug                Emit debugging messages
"""

import os
import sys
import configparser

import yaml
from docopt import docopt
from sqlalchemy import engine_from_config
import IPython

from fanart.backend import Backend
from fanart.models.tables import initialize_sql

class Const(str):
    """An unique object with a nice representation"""

FAIL = Const('FAIL')
ADMIN = Const('ADMIN')
GUEST = Const('GUEST')


def get_config_filename(arguments):
    filename, source = arguments['--config'], 'command line'
    if filename:
        return filename, source
    filename, source = os.environ.get('FANART_CONFIG_FILE'), 'environment'
    if filename:
        return filename, source
    for candidate in ['cli.ini', 'development.ini']:
        if os.path.exists(candidate):
            return candidate, source
    return None, None


def get_backend(arguments):
    filename, source = get_config_filename(arguments)
    if filename:
        config_filename = os.path.abspath(filename)
        del filename
        if not os.path.exists(config_filename):
            raise SystemExit('config file does not exist: {}'.format(
                config_filename))
        if arguments['--debug']:
            print('Using config file {} (from {})'.format(config_filename,
                                                          source),
                  file=sys.stderr)
        defaults = {'here': os.path.dirname(config_filename)}
        config = configparser.ConfigParser(defaults)
        config.read(config_filename)
    else:
        if arguments['--debug']:
            print('Cannot find config file', file=sys.stderr)
        config = None
    def get_value_with_source(
            argname, config_section, config_key, default=FAIL, boolean=False):
        if arguments[argname]:
            return arguments[argname], 'command line'
        try:
            section = config[config_section]
            if boolean:
                return section.getboolean(config_key), config_filename
            else:
                return section[config_key], config_filename
        except KeyError:
            pass
        return default, 'default'
    def get_value(argname, *args, **kwargs):
        value, source = get_value_with_source(argname, *args, **kwargs)
        if value is FAIL:
            if config:
                raise SystemExit('{} not given and not found in {}'.format(
                    argname, config_filename))
            else:
                raise SystemExit('{} not given, no config file found'.format(
                    argname))
        else:
            if arguments['--debug']:
                print('{}={} (from {})'.format(argname, value, source),
                    file=sys.stderr)
            return value
    db_url = get_value('--db-url', 'app:main', 'sqlalchemy.url')
    scratch_die = get_value('--scratch', 'app:main', 'fanart.scratch_dir')
    guest = get_value('--guest', 'cli', 'guest', False, boolean=True)
    user = get_value('--user', 'cli', 'user', GUEST if guest else ADMIN)

    engine = engine_from_config({'url': db_url}, prefix='')
    db = initialize_sql(engine)

    backend = Backend(db, scratch_die)
    if user is ADMIN:
        backend.login_admin()
    elif user is GUEST:
        pass
    else:
        backend.login(backend.users[user])

    return backend


def parse_argv(argv):
    return docopt(__doc__, argv)


def main(argv):
    arguments = parse_argv(argv)
    if arguments['--debug']:
        print(yaml.safe_dump({'Options': dict(arguments)}), file=sys.stderr)
    backend = get_backend(arguments)

    IPython.embed(
        usage='USAGE',
        banner2='Connected. The Backend is available in the variable `b`.',
        user_ns={
            'b': backend})


def entry_point():
    sys.exit(main(sys.argv[:1]))

if __name__ == '__main__':
    entry_point()
