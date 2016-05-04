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


def main():
    main_parser = argparse.ArgumentParser(description=("Setup and manage an "
                                                       "embedded development "
                                                       "infrastructure."))
    main_parser.add_argument("-v", "--verbose", action="store_true",
                             help="Increase output verbosity to INFO")
    main_parser.add_argument('--log', choices=['DEBUG', 'INFO', 'WARNING',
                                               'ERROR', 'CRITICAL'],
                             help="Modify log level (default is WARNING)")

    main_parser.add_argument('--version', action="store_true",
                             help="Print version and exit")

    subparsers = main_parser.add_subparsers(title='subcommands')
    bootstrap_parser = subparsers.add_parser('bootstrap',
                                             help='Bootstrap an initial image')
    bootstrap_parser.add_argument('config_file',
                                  type=argparse.FileType('r', encoding='UTF-8')
                                  )

    cli_args = main_parser.parse_args(sys.argv[1:])

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
