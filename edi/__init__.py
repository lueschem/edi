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
from setuptools_scm import get_version
import logging


def _setup_logging(cli_args):
    log_level = logging.WARNING

    if cli_args.log:
        log_level = getattr(logging, cli_args.log)

    if cli_args.verbose:
        # only make logging more verbose
        log_level = min([log_level, logging.INFO])

    logging.basicConfig(level=log_level)


class _HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print(_("* Command '{}':").format(choice))
                print(subparser.format_help())
        parser.exit()


def main():
    parser = argparse.ArgumentParser(description=("Setup and manage an "
                                                  "embedded development "
                                                  "infrastructure."),
                                     add_help=False)
    parser.add_argument('--help', action=_HelpAction, help="Show this help")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity to INFO")
    parser.add_argument('--log', choices=['DEBUG', 'INFO', 'WARNING',
                                          'ERROR', 'CRITICAL'],
                        help="Modify log level (default is WARNING)")

    parser.add_argument('--version', action="store_true",
                        help="Print version and exit")

    # TODO: set log level
    cli_args = parser.parse_args(sys.argv[1:])

    if cli_args.version:
        print(get_version(root='..', relative_to=__file__))
        sys.exit(0)

    _setup_logging(cli_args)

    logging.debug("Some debug message")
    logging.info("Some info message")
    logging.warning("Some warning message")
    logging.error("Some error message")

    print("Welcome to edi!")
    print(sys.argv)
