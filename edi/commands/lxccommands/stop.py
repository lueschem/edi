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

import hashlib
from edi.commands.lxc import Lxc
from edi.commands.lxccommands.lxcconfigure import Configure
from edi.lib.configurationparser import command_context
from edi.lib.helpers import print_success
from edi.lib.lxchelpers import stop_container, is_container_existing, is_container_running, delete_container


class Stop(Lxc):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "stop a running lxc container"
        description_text = "Stop a running lxc container."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self.run(cli_args.config_file)

    def run(self, config_file):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)

            # configure in any case since the container might be only partially configured
            Configure().run(self._result(), config_file)

            print("Going to stop lxc container {}.".format(self._result()))
            stop_container(self._result())
            print_success("Stopped lxc container {}.".format(self._result()))

        return self._result()

    def clean(self, config_file):
        self._setup_parser(config_file)

        if is_container_existing(self._result()):
            if is_container_running(self._result()):
                stop_container(self._result())

            delete_container(self._result())

            print_success("Deleted lxc container {}.".format(self._result()))

    def _result(self):
        # a generated container name
        return 'edi-tmp-{}'.format(hashlib.sha256(self.config.get_project_name().encode()
                                                  ).hexdigest()[:20])
