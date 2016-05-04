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

from edi.lib.edi_cmd import edi_cmd
import argparse
import logging


class bootstrapimage(edi_cmd):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "bootstrap an initial image"
        description_text = "Bootstrap an initial image."
        parser = subparsers.add_parser(cls.__name__,
                                       help=help_text,
                                       description=description_text)
        parser.add_argument('config_file',
                            type=argparse.FileType('r', encoding='UTF-8'))

    def run(self, cli_args):
        logging.info(("bootstrapping with config file {0} ..."
                      ).format(cli_args.config_file.name))
        logging.info(("bootstrapping with config file {0} ... done"
                      ).format(cli_args.config_file.name))
