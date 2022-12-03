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
from edi.lib.lxchelpers import stop_container, try_delete_container


class Stop(Lxc):

    def __init__(self):
        super().__init__()
        self._delete_container = True

    @classmethod
    def advertise(cls, subparsers):
        help_text = "stop a running lxc container"
        description_text = "Stop a running lxc container."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_options(parser, introspection=True, clean=True)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self._dispatch(*self._unpack_cli_args(cli_args), run_method=self._get_run_method(cli_args))

    def dry_run(self, config_file):
        return self._dispatch(config_file, run_method=self._dry_run)

    def _dry_run(self):
        return Configure().dry_run(self._result(), self.config.get_base_config_file())

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
        # configure in any case since the container might be only partially configured
        Configure().run(self._result(), self.config.get_base_config_file())

        print("Going to stop lxc container {}.".format(self._result()))
        stop_container(self._result(), timeout=self.config.get_lxc_stop_timeout())
        print_success("Stopped lxc container {}.".format(self._result()))

        return self._result()

    def clean_recursive(self, config_file, depth):
        self._delete_container = False  # Delete the container within the launch command!
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        if self._delete_container and try_delete_container(self._result(), self.config.get_lxc_stop_timeout()):
            print_success("Deleted lxc container {}.".format(self._result()))

        if self.clean_depth > 0:
            Configure().clean_recursive(self._result(), self.config.get_base_config_file(), self.clean_depth - 1)

    def _dispatch(self, config_file, run_method):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)
            return run_method()

    def _result(self):
        # a generated container name
        return 'edi-{}-{}'.format(hashlib.sha256(self.config.get_configuration_name().encode()).hexdigest()[:8],
                                  self.config.get_project_directory_hash())
