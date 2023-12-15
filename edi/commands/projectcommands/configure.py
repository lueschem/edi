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

import hashlib
from edi.commands.project import Project
from edi.commands.projectcommands.prepare import Prepare
from edi.lib.playbookrunner import PlaybookRunner
from edi.lib.helpers import print_success
from edi.lib.buildahhelpers import create_container, is_container_existing
from edi.lib.configurationparser import command_context
from edi.lib.commandrunner import ArtifactType, Artifact
from edi.lib.helpers import FatalError


class Configure(Project):

    def __init__(self):
        super().__init__()
        self.ansible_connection = 'buildah'
        self.collected_results = None

    @classmethod
    def advertise(cls, subparsers):
        help_text = "configure a buildah container using Ansible playbook(s)"
        description_text = "Configure a buildah container."
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

        container_name = self._get_container_artifact().location
        bootstrapped_rootfs = self._get_bootstrapped_rootfs(prepare_results)

        if not is_container_existing(container_name):
            print(f"Going to create buildah container '{container_name}'\n"
                  f"based on content of '{bootstrapped_rootfs}'.")
            create_container(container_name, bootstrapped_rootfs)

        print(f"Going to configure buildah container '{container_name}' - be patient.")

        playbook_runner = PlaybookRunner(self.config, self._get_container_artifact().location, self.ansible_connection)
        playbook_runner.run_all()

        print_success(f"Configured buildah container '{container_name}'.")

        collected_results = self._result()
        if collected_results:
            formatted_results = [f"{a.name}: {a.location}" for a in collected_results]
            print_success(("Completed the project configure command.\n"
                           "The following artifacts are now available:\n- {}".format('\n- '.join(formatted_results))))

        return collected_results

    def clean_recursive(self, config_file, depth):
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        # TODO: delete buildah container

        if self.clean_depth > 0:
            Prepare().clean_recursive(self.config.get_base_config_file(), self.clean_depth - 1)

    def _dispatch(self, config_file, run_method):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)
            return run_method()

    def _result(self):
        if not self.collected_results:
            self.collected_results = Prepare().result(self.config.get_base_config_file())
            self.collected_results.append(self._get_container_artifact())
        return self.collected_results

    def _get_container_artifact(self):
        container_name = "edi-{}-{}".format(
            hashlib.sha256(self.config.get_configuration_name().encode()).hexdigest()[:8],
            self.config.get_project_directory_hash())
        return Artifact(name="edi_buildah_container", location=container_name, type=ArtifactType.BUILDAH_CONTAINER)

    @staticmethod
    def _get_bootstrapped_rootfs(prepare_results):
        bootstrapped_rootfs = None
        expected_artifact = "edi_bootstrapped_rootfs"
        for result in prepare_results:
            if result.name is expected_artifact:
                if bootstrapped_rootfs:
                    raise FatalError((f"The project configure command expects exactly one {expected_artifact} "
                                      f"output artifact as a result the project prepare command (found multiple)!"))
                bootstrapped_rootfs = result

        if not bootstrapped_rootfs:
            raise FatalError((f"The project configure command expects a {expected_artifact} "
                              f"output artifact as a result the project prepare command!"))

        return bootstrapped_rootfs

    def result(self, config_file):
        return self._dispatch(config_file, run_method=self._result)
