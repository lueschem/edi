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

from edi.commands.qemu import Qemu
from edi.lib.helpers import print_success


class Fetch(Qemu):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "fetch a qemu binary"
        description_text = "Fetch a qemu binary."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        result = self.run(cli_args.config_file)

    def run(self, config_file):
        self._setup_parser(config_file)

        print("Going to fetch qemu binary")

        print_success("Fetched qemu binary {}.".format(self._result()))
        return self._result()

    def _result(self):
        return "None"
