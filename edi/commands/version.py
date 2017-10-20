# -*- coding: utf-8 -*-
# Copyright (C) 2017 Matthias Luescher
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

from edi.lib.edicommand import EdiCommand
from edi.lib.versionhelpers import get_edi_version


class Version(EdiCommand):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "print the program version"
        description_text = "Print the program version."
        subparsers.add_parser(cls._get_short_command_name(),
                              help=help_text,
                              description=description_text)

    def run_cli(self, _):
        version = self.run()
        print(version)

    @staticmethod
    def run():
        return get_edi_version()
