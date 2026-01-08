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

import os
import logging
import tempfile
import yaml
import jinja2
import stat
from codecs import open
from collections import namedtuple

from edi.lib.artifact import ArtifactType, Artifact
from edi.lib.helpers import (chown_to_user, FatalError, get_workdir, get_artifact_dir,
                             create_artifact_dir, print_success)
from edi.lib.shellhelpers import run, safely_remove_artifacts_folder
from edi.lib.configurationparser import remove_passwords
from edi.lib.yamlhelpers import LiteralString
from edi.lib.podmanhelpers import is_image_existing, try_delete_image, untag_image

Command = namedtuple("Command", "script_name, script_content, node_name, resolved_template_path, "
                                "node_dictionary, config_node, output_artifacts")


def find_artifact(artifact_collection, expected_artifact_name, command_name, previous_command_name):
    identified_artifact = None
    for artifact in artifact_collection:
        if artifact.name == expected_artifact_name:
            if identified_artifact:
                raise FatalError((f"The project {command_name} command expects exactly one '{expected_artifact_name}' "
                                  f"output artifact as a result the project {previous_command_name} command "
                                  f"(found multiple)!"))
            identified_artifact = artifact

    if not identified_artifact:
        raise FatalError((f"The project {command_name} command expects a '{expected_artifact_name}' "
                          f"output artifact as a result the project {previous_command_name} command!"))

    return identified_artifact


class CommandRunner:

    def __init__(self, config, section, input_artifacts):
        assert input_artifacts is None or type(input_artifacts) is Artifact or type(input_artifacts) is list
        self.config = config
        self.config_section = section
        if not input_artifacts:
            self._input_artifacts = list()
        elif type(input_artifacts) is Artifact:
            if input_artifacts.location:
                self._input_artifacts = list()
                self._input_artifacts.append(input_artifacts)
            else:
                self._input_artifacts = list()
        else:
            assert type(input_artifacts) is list
            self._input_artifacts = input_artifacts.copy()

    def run(self):
        workdir = get_workdir()
        create_artifact_dir()

        commands = self._get_commands()

        for command in commands:
            if self._are_all_artifacts_available(command.output_artifacts):
                logging.info(('''Artifacts for command '{}' are already there. '''
                              '''Delete them to regenerate them.'''
                              ).format(command.node_name))
            else:
                with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
                    chown_to_user(tmpdir)
                    require_root = command.config_node.get('require_root', False)

                    logging.info(("Running command {} located in "
                                  "{} with dictionary:\n{}"
                                  ).format(command.node_name, command.resolved_template_path,
                                           yaml.dump(remove_passwords(command.node_dictionary),
                                                     default_flow_style=False)))

                    command_file = self._flush_command_file(tmpdir, command.script_name, command.script_content)
                    self._run_command(command_file, require_root)
                    self._post_process_artifacts(command.node_name, command.output_artifacts)

        return self._result(commands)

    def require_real_root(self):
        commands = self._get_commands()

        for command in commands:
            if self._require_real_root(command.config_node.get('require_root', False)):
                return True

        return False

    @staticmethod
    def _require_real_root(config_value):
        if type(config_value) is bool:
            return config_value
        elif config_value == "fakeroot" or config_value == "unshare":
            return False
        else:
            raise FatalError('Invalid value for "require_root". It must be either "True", "False", "fakeroot" or'
                             ' "unshare".')

    def require_real_root_for_clean(self):
        for command in self._get_commands():
            if (self._require_real_root(command.config_node.get('require_root', False))
                    and self._is_root_required_for_removal(command.output_artifacts)):
                return True

        return False

    def get_plugin_report(self):
        result = {}

        commands = self._get_commands()

        if commands:
            result[self.config_section] = []

        for command in commands:
            plugin_info = {command.node_name: {'path': command.resolved_template_path,
                                               'dictionary': command.node_dictionary,
                                               'result': LiteralString(command.script_content)}}

            result[self.config_section].append(plugin_info)

        return result

    def clean(self):
        commands = self._get_commands()
        for command in commands:
            for _, artifact in command.output_artifacts.items():
                if artifact.type is ArtifactType.PATH:
                    if not str(get_workdir()) in str(artifact.location):
                        raise FatalError(('Output artifact {} is not within the current working directory!'
                                          ).format(artifact.location))

                    if os.path.isfile(artifact.location):
                        logging.info("Removing '{}'.".format(artifact.location))
                        os.remove(artifact.location)
                        print_success("Removed image file artifact {}.".format(artifact.location))
                    elif os.path.isdir(artifact.location):
                        safely_remove_artifacts_folder(artifact.location,
                                                       sudo=self._require_real_root(
                                                           command.config_node.get('require_root', False)))
                        print_success("Removed image directory artifact {}.".format(artifact.location))
                elif artifact.type in [ArtifactType.PODMAN_IMAGE, ArtifactType.PODMAN_IMAGE_ROOT]:
                    image_name = artifact.location
                    require_sudo = artifact.type is ArtifactType.PODMAN_IMAGE_ROOT
                    if is_image_existing(image_name, sudo=require_sudo):
                        if try_delete_image(image_name, sudo=require_sudo):
                            print_success(f"Removed podman image {artifact.location}.")
                        else:
                            logging.info(f"Podman image '{artifact.location}' is still in use, going to untag it.")
                            untag_image(image_name, sudo=require_sudo)
                            print_success(f"Untagged podman image {artifact.location}.")
                else:
                    raise FatalError(f"Unhandled removal of artifact type '{artifact.type}'.")

    def result(self):
        commands = self._get_commands()
        return self._result(commands)

    @staticmethod
    def _run_command(command_file, require_root):
        cmd = []
        if require_root == 'fakeroot':
            cmd.extend(['fakeroot', '--'])
        elif require_root == 'unshare':
            cmd.extend(['buildah', 'unshare', '--'])

        cmd.extend(['sh', '-c', command_file])
        run(cmd, log_threshold=logging.INFO, sudo=CommandRunner._require_real_root(require_root))

    def _get_commands(self):
        commands = self.config.get_ordered_path_items(self.config_section)
        augmented_commands = []
        artifacts = dict()
        for a in self._input_artifacts:
            artifacts[a.name] = a

        for name, path, dictionary, raw_node in commands:
            output = raw_node.get('output')
            if type(output) is not dict:
                raise FatalError(('''The output specification in command node '{}' is not a key value dictionary.'''
                                  ).format(name))

            new_artifacts = dict()
            for artifact_key, artifact_item in output.items():
                new_artifacts[artifact_key] = self._get_artifact(name, artifact_key, artifact_item)

            artifacts.update(new_artifacts)
            dictionary.update({key: val.location for key, val in artifacts.items()})
            filename, content = self._render_command_file(path, dictionary)
            new_command = Command(script_name=filename, script_content=content, node_name=name,
                                  resolved_template_path=path, node_dictionary=dictionary, config_node=raw_node,
                                  output_artifacts=new_artifacts)
            augmented_commands.append(new_command)

        return augmented_commands

    @staticmethod
    def _get_artifact(node_name, artifact_key, artifact_item):
        if type(artifact_item) is dict:
            artifact_location = artifact_item.get('location', '')
            artifact_type_string = artifact_item.get('type', 'path')
            try:
                artifact_type = ArtifactType(artifact_type_string)
            except ValueError:
                raise FatalError((f"The specified output artifact '{artifact_key}' within the "
                                  f"command node '{node_name}' has an invalid artifact type '{artifact_type_string}'."))
        else:
            artifact_location = artifact_item
            artifact_type = ArtifactType.PATH

        if not artifact_location:
            raise FatalError((f"The specified output artifact '{artifact_key}' within the "
                              f"command node '{node_name}' must not be empty."))

        if artifact_type is ArtifactType.PATH:
            if str(artifact_location) != str(os.path.basename(artifact_location)):
                raise FatalError((('''The specified output artifact '{}' within the '''
                                   '''command node '{}' is invalid. '''
                                   '''The output shall be a file or a folder (no '/' in string).''')
                                  ).format(artifact_key, node_name))
            artifact_location = os.path.join(get_artifact_dir(), artifact_location)

        return Artifact(name=artifact_key, location=str(artifact_location), type=artifact_type)

    @staticmethod
    def _are_all_artifacts_available(artifacts):
        for _, artifact in artifacts.items():
            if artifact.type is ArtifactType.PATH:
                if not os.path.isfile(artifact.location) and not os.path.isdir(artifact.location):
                    return False
            elif artifact.type in [ArtifactType.PODMAN_IMAGE, ArtifactType.PODMAN_IMAGE_ROOT]:
                require_sudo = artifact.type is ArtifactType.PODMAN_IMAGE_ROOT
                if not is_image_existing(artifact.location, sudo=require_sudo):
                    return False
            else:
                raise FatalError(f"Unhandled presence checking for artifact type '{artifact.type}'.")

        return True

    @staticmethod
    def _is_root_required_for_removal(artifacts):
        for _, artifact in artifacts.items():
            if artifact.type is ArtifactType.PATH and os.path.isdir(artifact.location):
                return True
            if artifact.type is ArtifactType.PODMAN_IMAGE_ROOT:
                # Unable to check presence as we might not be running as root.
                return True

        return False

    @staticmethod
    def _post_process_artifacts(command_name, expected_artifacts):
        for _, artifact in expected_artifacts.items():
            if artifact.type is ArtifactType.PATH:
                if not os.path.isfile(artifact.location) and not os.path.isdir(artifact.location):
                    raise FatalError(('''The command '{}' did not generate '''
                                      '''the specified output artifact '{}'.'''.format(command_name,
                                                                                       artifact.location)))
                elif os.path.isfile(artifact.location):
                    chown_to_user(artifact.location)
            elif artifact.type in [ArtifactType.PODMAN_IMAGE, ArtifactType.PODMAN_IMAGE_ROOT]:
                require_sudo = artifact.type is ArtifactType.PODMAN_IMAGE_ROOT
                if not is_image_existing(artifact.location, sudo=require_sudo):
                    raise FatalError(('''The command '{}' did not generate '''
                                      '''the specified podman image '{}'.'''.format(command_name,
                                                                                    artifact.location)))
            else:
                raise FatalError(f"Missing postprocessing rule for artifact type '{artifact.type}'.")

    @staticmethod
    def _render_command_file(input_file, dictionary):
        with open(input_file, encoding="UTF-8", mode="r") as template_file:
            template = jinja2.Template(template_file.read())
            result = template.render(dictionary)

        filename = os.path.basename(input_file)
        return filename, result

    @staticmethod
    def _flush_command_file(output_dir, filename, content):
        output_file = os.path.join(output_dir, filename)
        with open(str(output_file), encoding="UTF-8", mode="w") as result_file:
            result_file.write(content)

        st = os.stat(output_file)
        os.chmod(output_file, st.st_mode | stat.S_IEXEC)

        chown_to_user(output_file)

        return output_file

    def _result(self, commands):
        all_artifacts = self._input_artifacts
        for command in commands:
            for _, artifact in command.output_artifacts.items():
                all_artifacts.append(artifact)

        return all_artifacts
