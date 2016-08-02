# Copyright 2015, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import os

from requests.exceptions import RequestException

from tower_cli import __version__
from tower_cli.api import client
from tower_cli.utils.decorators import command
from tower_cli.utils.exceptions import TowerCLIError
from tower_cli.utils import exceptions as exc
from tower_cli.conf import Parser


@command
def version():
    """Display version information."""

    # Attempt to connect to the Ansible Tower server.
    # If we succeed, assign the version variable; if not, 
    # set no-connection flag.
    try:
        r = client.get('/config/')
    except (RequestException, exc.ConnectionError):
        tower_version = None
        no_conn_flag = True
    else:
        tower_version = r.json()['version']
        no_conn_flag = False

    # Check all possible config file locations. Update all file
    # contents if version is get from remote host. If not, update
    # version variable with the highest priority config file.
    for filename in ['.tower_cli.cfg',
                     os.path.expanduser('~/.tower_cli.cfg'),
                     '/etc/tower_cli.cfg']:
        if os.path.isfile(filename):
            parser = Parser()
            parser.read(filename)
            if not parser.has_section('remote'):
                parser.add_section('remote')
            if no_conn_flag:
                if tower_version is None and \
                   parser.has_option('remote', 'version'):
                    tower_version = parser.get('remote', 'version')
            if tower_version is not None:
                parser.set('remote', 'version', tower_version)
                with open(filename, 'w') as config_file:
                    parser.write(config_file)

    # Print out the current or last recorded tower version.
    if tower_version is None:
        raise TowerCLIError('Could not connect to Ansible Tower and no'
                            ' previous record available.')
    else:
        if no_conn_flag:
            click.echo('Fetching previous record due to connection error,'
                       ' the result might be deprecated...')
        click.echo('Ansible Tower %s' % tower_version)

    # Print out the current version of Tower CLI.
    click.echo('Tower CLI %s' % __version__)
