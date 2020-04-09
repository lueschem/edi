# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
#
# Authors:
#  Matthias Luescher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.

import sys
import argparse
import argcomplete
import logging
import requests
from edi.commands import clean, config, image, lxc, qemu, target, version, documentation  # noqa: ignore=F401
from edi.lib.commandfactory import get_sub_commands, get_command
from edi.lib.helpers import print_error_and_exit, FatalError
from edi.lib.edicommand import EdiCommand
from subprocess import CalledProcessError


def _setup_logging(cli_args):
    log_level = logging.WARNING

    if cli_args.log:
        log_level = getattr(logging, cli_args.log)

    if cli_args.verbose:
        # only make logging more verbose
        log_level = min([log_level, logging.INFO])

    logging.basicConfig(level=log_level)


def _setup_command_line_interface():
    parser = argparse.ArgumentParser(description=("Setup and manage an "
                                                  "embedded development "
                                                  "infrastructure."))
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity to INFO")
    parser.add_argument('--log', choices=['DEBUG', 'INFO', 'WARNING',
                                          'ERROR', 'CRITICAL'],
                        help="modify log level (default is WARNING)")

    subparsers = parser.add_subparsers(title='commands',
                                       dest="command_name")

    for _, command in get_sub_commands().items():
        command.advertise(subparsers)
    argcomplete.autocomplete(parser)
    return parser


def main():
    try:
        cli_interface = _setup_command_line_interface()
        cli_args = cli_interface.parse_args(sys.argv[1:])
        _setup_logging(cli_args)

        if cli_args.command_name is None:
            raise FatalError("Missing command. Use 'edi --help' for help.")

        command_name = "{0}.{1}".format(EdiCommand._get_command_name(),
                                        cli_args.command_name)
        get_command(command_name)().run_cli(cli_args)
    except FatalError as fatal_error:
        print_error_and_exit(fatal_error.message)
    except KeyboardInterrupt:
        print_error_and_exit("Command interrupted by user.")
    except CalledProcessError as subprocess_error:
        print_error_and_exit("{}\nFor more information increase the log level.".format(subprocess_error))
    except requests.exceptions.SSLError as ssl_error:
        print_error_and_exit("{}\nPlease verify your ssl/proxy setup.".format(ssl_error))
    except requests.exceptions.ConnectionError as connection_error:
        print_error_and_exit(("{}\nPlease verify your internet connectivity and the requested url."
                              ).format(connection_error))
