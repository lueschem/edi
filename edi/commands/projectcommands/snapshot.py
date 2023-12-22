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

import os
import logging
from edi.commands.project import Project
from edi.commands.projectcommands.configure import Configure
from edi.lib.commandrunner import Artifact, ArtifactType, find_artifact
from edi.lib.helpers import print_success, get_artifact_dir
from edi.lib.buildahhelpers import extract_container_rootfs
from edi.lib.configurationparser import command_context


class Snapshot(Project):

    def __init__(self):
        super().__init__()
        self._configure_results = None

    @classmethod
    def advertise(cls, subparsers):
        help_text = "export a snapshot of an edi project container"
        description_text = "Export a snapshot of an edi project container as an archive."
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
        return Configure().dry_run(self.config.get_base_config_file())

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
        snapshot_archive = self._get_snapshot_artifact().location
        if os.path.isfile(snapshot_archive):
            logging.info(f"'{snapshot_archive}' is already there. Delete it to regenerate it.")
        else:
            self._configure_results = Configure().run(self.config.get_base_config_file())
            project_container = find_artifact(self._configure_results, "edi_project_container",
                                              "snapshot", "configure").location

            print("Going to extract the root file system of the project container.")
            extract_container_rootfs(project_container, snapshot_archive)

        collected_results = self._result()
        if collected_results:
            formatted_results = [f"{a.name}: {a.location}" for a in collected_results]
            print_success(("Completed the project snapshot command.\n"
                           "The following artifacts are now available:\n- {}".format('\n- '.join(formatted_results))))

        return collected_results

    def clean_recursive(self, config_file, depth):
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        snapshot_archive = self._get_snapshot_artifact().location
        if os.path.isfile(snapshot_archive):
            logging.info(f"Removing '{snapshot_archive}'.")
            os.remove(snapshot_archive)
            print_success(f"Removed root file system snapshot '{snapshot_archive}'.")

        if self.clean_depth > 0:
            Configure().clean_recursive(self.config.get_base_config_file(), self.clean_depth - 1)

    def _dispatch(self, config_file, run_method):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)
            return run_method()

    def _result(self):
        if not self._configure_results:
            self._configure_results = Configure().result(self.config.get_base_config_file())

        all_results = self._configure_results.copy()
        all_results.append(self._get_snapshot_artifact())
        return all_results

    def result(self, config_file):
        return self._dispatch(config_file, run_method=self._result)

    def _get_snapshot_artifact(self):
        snapshot_name = f"{self.config.get_configuration_name()}_snapshot.tar"
        return Artifact(name="edi_configured_rootfs",
                        location=str(os.path.join(get_artifact_dir(), snapshot_name)),
                        type=ArtifactType.PATH)
