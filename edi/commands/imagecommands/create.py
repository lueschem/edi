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

from edi.commands.image import Image
from edi.commands.lxccommands.export import Export
from edi.lib.commandrunner import CommandRunner
from edi.lib.configurationparser import command_context
from edi.lib.helpers import print_success


class Create(Image):

    def __init__(self):
        super().__init__()
        self.section = 'postprocessing_commands'

    @classmethod
    def advertise(cls, subparsers):
        help_text = "create a re-distributable image"
        description_text = "Create a re-distributable image."
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
        plugins.update(Export().dry_run(self.config.get_base_config_file()))
        command_runner = CommandRunner(self.config, self.section, self._input_artifact())
        plugins.update(command_runner.get_plugin_report())
        return plugins

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
        command_runner = CommandRunner(self.config, self.section, self._input_artifact())

        if command_runner.require_root():
            self._require_sudo()

        Export().run(self.config.get_base_config_file())

        print("Going to post process image - be patient.")

        result = command_runner.run()

        print_success(("Completed the image creation post processing commands.\n"
                       "The following artifacts are now available:\n- {}".format('\n- '.join(result))))
        return result

    def clean_recursive(self, config_file, depth):
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        command_runner = CommandRunner(self.config, self.section, self._input_artifact())
        if command_runner.require_root_for_clean():
            self._require_sudo()
        command_runner.clean()

        if self.clean_depth > 0:
            Export().clean_recursive(self.config.get_base_config_file(), self.clean_depth - 1)

    def _dispatch(self, config_file, run_method):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)
            return run_method()

    def _input_artifact(self):
        return Export().result(self.config.get_base_config_file())
