# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Lüscher
#
# Authors:
#  Matthias Lüscher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.

import sys
import argparse
import argcomplete
from setuptools_scm import get_version
import logging
from edi.commands import *
from edi.lib.command_factory import command_registry


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

    parser.add_argument('--version', action="store_true",
                        help="print version and exit")

    subparsers = parser.add_subparsers(title='subcommands',
                                       dest="command_name")

    for _, command in command_registry.items():
        command.advertise(subparsers)
    argcomplete.autocomplete(parser)
    return parser


def main():
    cli_interface = _setup_command_line_interface()
    cli_args = cli_interface.parse_args(sys.argv[1:])
    _setup_logging(cli_args)

    if cli_args.version:
        print(get_version(root='..', relative_to=__file__))
        sys.exit(0)

    if cli_args.command_name is None:
        cli_interface.print_help()
        sys.exit(1)

    command_registry[cli_args.command_name]().run(cli_args)
