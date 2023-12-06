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
from edi.commands.projectcommands.prepare import Prepare
from edi.lib.playbookrunner import PlaybookRunner
from edi.lib.helpers import print_success
from edi.lib.configurationparser import command_context
from edi.lib.commandrunner import ArtifactType, Artifact
from edi.lib.helpers import FatalError


class Configure(Project):

    def __init__(self):
        super().__init__()
        self.ansible_connection = 'buildah'
        self.output_artifact = None

    @classmethod
    def advertise(cls, subparsers):
        help_text = "configure a container using Ansible playbook(s)"
        description_text = "Configure a container."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_options(parser, introspection=True, clean=True)
        cls._require_config_file(parser)

    @staticmethod
    def _unpack_cli_args(cli_args):
        return [cli_args.config_file]

    def run_cli(self, cli_args):
        self._dispatch(*self._unpack_cli_args(cli_args), run_method=self._get_run_method(cli_args))

    def dry_run(self, config_file):
        return self._dispatch(config_file, run_method=self._dry_run)

    def _dry_run(self):
        plugins = {}
        plugins.update(Prepare().dry_run(self.config.get_base_config_file()))
        playbook_runner = PlaybookRunner(self.config, self._result(), self.ansible_connection)
        plugins.update(playbook_runner.get_plugin_report())
        return plugins

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
        prepare_results = Prepare().run(self.config.get_base_config_file())
        self.output_artifact = self._extract_container(prepare_results)

        print("Going to configure container {} - be patient.".format(self._result().url))

        playbook_runner = PlaybookRunner(self.config, self._result().url, self.ansible_connection)
        playbook_runner.run_all()

        print_success("Configured container {}.".format(self._result()))
        return self._result()

    def clean_recursive(self, config_file, depth):
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        if self.clean_depth > 0:
            Prepare().clean_recursive(self.config.get_base_config_file(), self.clean_depth - 1)

    def _dispatch(self, config_file, run_method):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)
            return run_method()

    def _result(self):
        if not self.output_artifact:
            prepare_results = Prepare().result(self.config.get_base_config_file())

            self.output_artifact = self._extract_container(prepare_results)

        return self.output_artifact

    @staticmethod
    def _extract_container(prepare_results):
        new_container = None
        for result in prepare_results:
            if new_container:
                raise FatalError(("The project configure command expects exactly one buildah container "
                                  "as a result of the project prepare command (found multiple)!"))

            if result.type is ArtifactType.BUILDAH_CONTAINER:
                new_container = Artifact("configured_container", f"{result.url}_out", result.type)

        if not new_container:
            raise FatalError(("The project configure command expects a buildah container as a result of the "
                              "project prepare command!"))

        return new_container

    def result(self, config_file):
        return self._dispatch(config_file, run_method=self._result)
