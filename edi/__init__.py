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
    parser = argparse.ArgumentParser(description="Setup and manage an embedded development infrastructure.",
                                     add_help=False)
    parser.add_argument('--help', action=_HelpAction, help="Show this help")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase output verbosity (2 levels)")

    parser.add_argument('--version', action="store_true", help="Print version and exit")

    # TODO: set log level
    parser.parse_args(sys.argv[1:])
    
    print("Welcome to edi!") 
    print(sys.argv)
