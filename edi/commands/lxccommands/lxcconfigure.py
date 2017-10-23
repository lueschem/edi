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

from edi.commands.lxc import Lxc
from edi.commands.lxccommands.profile import Profile
from edi.commands.lxccommands.launch import Launch
from edi.lib.playbookrunner import PlaybookRunner
from edi.lib.helpers import print_success
from edi.lib.sharedfoldercoordinator import SharedFolderCoordinator
from edi.lib.lxchelpers import apply_profiles


class Configure(Lxc):

    def __init__(self):
        self.container_name = ""
        self.ansible_connection = 'lxd'

    @classmethod
    def advertise(cls, subparsers):
        help_text = "configure a LXC container"
        description_text = "Configure a LXC container."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        parser.add_argument('container_name')
        cls._require_config_file(parser)

    @staticmethod
    def _unpack_cli_args(cli_args):
        return [cli_args.container_name, cli_args.config_file]

    def run_cli(self, cli_args):
        self._dispatch(*self._unpack_cli_args(cli_args), run_method=self._get_run_method(cli_args))

    def dry_run(self, container_name, config_file):
        return self._dispatch(container_name, config_file, run_method=self._dry_run)

    def _dry_run(self):
        plugins = {}
        plugins.update(Launch().dry_run(self.container_name, self.config.get_base_config_file()))
        playbook_runner = PlaybookRunner(self.config, self._result(), self.ansible_connection)
        plugins.update(playbook_runner.get_plugin_report())
        plugins.update(Profile().dry_run(self.config.get_base_config_file(), include_post_config_profiles=True))
        return plugins

    def run(self, container_name, config_file):
        return self._dispatch(container_name, config_file, run_method=self._run)

    def _run(self):
        Launch().run(self.container_name, self.config.get_base_config_file())

        print("Going to configure container {} - be patient.".format(self._result()))

        playbook_runner = PlaybookRunner(self.config, self._result(), self.ansible_connection)
        playbook_runner.run_all()

        sfc = SharedFolderCoordinator(self.config)
        sfc.create_host_folders()
        sfc.verify_container_mountpoints(self.container_name)

        profiles = Profile().run(self.config.get_base_config_file(), include_post_config_profiles=True)
        # TODO: stop container if profiles need to be updated
        apply_profiles(self.container_name, profiles)
        # TODO: restart container if needed

        print_success("Configured container {}.".format(self._result()))
        return self._result()

    def _dispatch(self, container_name, config_file, run_method):
        self._setup_parser(config_file)
        self.container_name = container_name
        return run_method()

    def _result(self):
        return self.container_name
