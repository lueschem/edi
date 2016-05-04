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

from edi.lib.command_factory import command_factory
import argparse


class bootstrap_cmd(metaclass=command_factory):

    @staticmethod
    def advertise(subparsers):
        parser = subparsers.add_parser(bootstrap_cmd.name(),
                                       help='Bootstrap an initial image',
                                       description=("Bootstrap an initial "
                                                    "image."))
        parser.add_argument('config_file',
                            type=argparse.FileType('r', encoding='UTF-8'))

    @staticmethod
    def name():
        return "bootstrap"

    def run(self, cli_args):
        print(("bootstrapping with config file {0} ..."
               ).format(cli_args.config_file.name))
        print("done")
