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
import logging
import os
from edi.commands.project import Project
from edi.commands.projectcommands.prepare import Prepare
from edi.lib.playbookrunner import PlaybookRunner
from edi.lib.helpers import print_success, get_artifact_dir, create_artifact_dir
from edi.lib.shellhelpers import run
from edi.lib.buildahhelpers import create_container, delete_container, is_container_existing
from edi.lib.configurationparser import command_context
from edi.lib.commandrunner import find_artifact
from edi.lib.artifact import ArtifactType, Artifact


class Configure(Project):

    def __init__(self):
        super().__init__()
        self.clean_depth = 1
        self.ansible_connection = 'buildah'
        self._prepare_results = None

    @classmethod
    def advertise(cls, subparsers):
        help_text = "configure a project container using Ansible playbook(s)"
        description_text = "Configure a project container."
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
        if self._needs_processing():
            container_name = self._get_container_artifact().location

            if is_container_existing(container_name):
                logging.info(f"Project container {container_name} is already existing. "
                             f"Delete the container to get it re-created from scratch.")
            else:
                self._prepare_results = Prepare().run(self.config.get_base_config_file())

                bootstrapped_rootfs = find_artifact(self._prepare_results, "edi_bootstrapped_rootfs",
                                                    "configure", "prepare")

                print(f"Going to create project container '{container_name}'\n"
                      f"based on content of '{bootstrapped_rootfs.location}'.")
                create_container(container_name, bootstrapped_rootfs)

            seal_file = self._get_seal_artifact().location

            if os.path.exists(seal_file):
                logging.info(f"Project container {container_name} is already fully configured. "
                             f"Delete {seal_file} to get it re-configured.")
            else:
                print(f"Going to configure project container '{container_name}' - be patient.")

                playbook_runner = PlaybookRunner(self.config, container_name, self.ansible_connection)
                playbook_runner.run_all()
                create_artifact_dir()
                run(["touch", seal_file])

            print_success(f"Configured project container '{container_name}'.")

        collected_results = self._result()
        if collected_results:
            formatted_results = [f"{a.name}: {a.location}" for a in collected_results]
            print_success(("Completed the project configure command.\n"
                           "The following artifacts are now available:\n- {}".format('\n- '.join(formatted_results))))

        return collected_results

    def clean_recursive(self, config_file, depth):
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        seal_file = self._get_seal_artifact().location
        if os.path.exists(seal_file):
            os.remove(seal_file)
            print_success(f"Deleted seal file '{seal_file}'.")

        if self.clean_depth > 0:
            container_name = self._get_container_artifact().location
            if is_container_existing(container_name):
                delete_container(container_name)
                print_success(f"Deleted project container '{container_name}'.")

        if self.clean_depth > 1:
            Prepare().clean_recursive(self.config.get_base_config_file(), self.clean_depth - 2)

    def _dispatch(self, config_file, run_method):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)
            return run_method()

    def _result(self):
        if not self._needs_processing():
            return list()

        if not self._prepare_results:
            self._prepare_results = Prepare().result(self.config.get_base_config_file())

        all_results = self._prepare_results.copy()
        all_results.append(self._get_container_artifact())
        all_results.append(self._get_seal_artifact())
        return all_results

    def _needs_processing(self):
        return self.config.has_preprocessing_commands_node() or self.config.has_playbooks_node()

    def result(self, config_file):
        return self._dispatch(config_file, run_method=self._result)

    def _get_container_artifact(self):
        container_name = "edi-{}-{}".format(
            hashlib.sha256(self.config.get_configuration_name().encode()).hexdigest()[:8],
            self.config.get_project_directory_hash())
        return Artifact(name="edi_project_container", location=container_name, type=ArtifactType.BUILDAH_CONTAINER)

    def _get_seal_artifact(self):
        seal_artifact = f"{self.config.get_configuration_name()}.seal"
        return Artifact(name="edi_project_container_seal",
                        location=str(os.path.join(get_artifact_dir(), seal_artifact)),
                        type=ArtifactType.PATH)
