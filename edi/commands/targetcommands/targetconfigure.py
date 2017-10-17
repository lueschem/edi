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

from edi.commands.target import Target
from edi.lib.playbookrunner import PlaybookRunner
from edi.lib.helpers import print_success


class Configure(Target):

    def __init__(self):
        self.ip_address = None

    @classmethod
    def advertise(cls, subparsers):
        help_text = "(re)configure an edi target system"
        description_text = "(Re)configure an edi target system."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        parser.add_argument('ip_address')
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self.run(cli_args.ip_address, cli_args.config_file,
                 introspection_method=self._get_introspection_method(
                     cli_args, ['playbooks']))

    def run(self, ip_address, config_file, introspection_method=None):
        self._setup_parser(config_file)
        self.ip_address = ip_address

        if introspection_method:
            self._print(introspection_method())
            return self._result()

        print("Going to configure target system ({}) - be patient.".format(self._result()))

        playbook_runner = PlaybookRunner(self.config, self._result(), "ssh")
        playbook_runner.run_all()

        print_success("Configured target system ({}).".format(self._result()))
        return self._result()

    def _result(self):
        return self.ip_address
