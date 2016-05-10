# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
#
# Authors:
#  Matthias Luescher
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
from edi.lib.configuration_parser import ConfigurationParser
import argparse
import os
from edi.lib.helpers import print_error_and_exit


class edi_cmd(metaclass=command_factory):

    config_parser = None

    def __init__(self, cli_args):
        if edi_cmd.config_parser is None:
            edi_cmd.config_parser = ConfigurationParser(cli_args.config_file)

    @staticmethod
    def require_config_file(parser):
        parser.add_argument('config_file',
                            type=argparse.FileType('r', encoding='UTF-8'))

    def require_sudo(self):
        if os.getuid() != 0:
            print_error_and_exit(("The subcommand '{0}' requires superuser "
                                  "privileges.\n"
                                  "Use 'sudo edi {0} ...'."
                                  ).format(type(self).__name__))
