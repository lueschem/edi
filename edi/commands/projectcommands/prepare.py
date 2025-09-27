# -*- coding: utf-8 -*-
# Copyright (C) 2023 Matthias Luescher
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

from edi.commands.project import Project
from edi.lib.commandrunner import CommandRunner
from edi.lib.configurationparser import command_context
from edi.lib.helpers import print_success


class Prepare(Project):

    def __init__(self):
        super().__init__()
        self.section = 'preprocessing_commands'

    @classmethod
    def advertise(cls, subparsers):
        help_text = "prepare an edi project configuration"
        description_text = "Prepare the artifacts for an edi project configuration."
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
        plugins = {}
        command_runner = CommandRunner(self.config, self.section, None)
        plugins.update(command_runner.get_plugin_report())
        return plugins

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
        command_runner = CommandRunner(self.config, self.section, None)

        if command_runner.require_real_root():
            self._require_sudo()

        print("Going to pre process project - be patient.")

        result = command_runner.run()

        if result:
            formatted_results = [f"{a.name}: {a.location}" for a in result]
            print_success(("Completed the project preparation pre processing commands.\n"
                           "The following artifacts are now available:\n- {}".format('\n- '.join(formatted_results))))
        return result

    def clean_recursive(self, config_file, depth):
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        command_runner = CommandRunner(self.config, self.section, None)
        if command_runner.require_real_root_for_clean():
            self._require_sudo()
        command_runner.clean()

    def _dispatch(self, config_file, run_method):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file, 2)
            return run_method()

    def result(self, config_file):
        return self._dispatch(config_file, run_method=self._result)

    def _result(self):
        command_runner = CommandRunner(self.config, self.section, None)
        return command_runner.result()
