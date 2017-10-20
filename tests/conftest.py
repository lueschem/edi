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

from pytest import fixture
import os
from edi.lib.helpers import copy_tree, get_user, get_hostname


def pytest_addoption(parser):
    parser.addoption("--all", action="store_true",
                     help="include all tests - even those that rely on lxc, ansible, ...")
    parser.addoption("--lxc", action="store_true",
                     help="include tests that rely on lxc availability")
    parser.addoption("--ansible", action="store_true",
                     help="include tests that rely on ansible availability")
    parser.addoption("--debootstrap", action="store_true",
                     help="include tests that rely on debootstrap availability")


@fixture
def datadir(tmpdir, request):
    '''
    Move data from tests/data/TESTNAME into a temporary directory
    so that the test can modify its data set.
    '''
    test_subdir = os.path.basename(os.path.splitext(request.module.__file__)[0])
    test_data = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', test_subdir))

    if os.path.isdir(test_data):
        copy_tree(str(test_data), str(tmpdir))

    return tmpdir


sample_file = """
---
general:
    edi_compression:        gz

shared_folders:
    skip_me:
        folder:             skip
        mountpoint:         me
    workspace:
        folder:             work
        mountpoint:         mywork

bootstrap:
    tool:                   debootstrap
    architecture:           amd64
    repository:             deb http://ftp.ch.debian.org/debian/ jessie main

playbooks:
    10_base_system:
        path:               playbooks/foo.yml
        parameters:
            kernel_package: linux-image-amd64
            message:        some message
    20_networking:
        path:               playbooks/bar.yml

postprocessing_commands:
    10_first_step:
        path:               commands/command
        output:             first.txt
        parameters:
            message:        "*first step*"
    20_second_step:
        path:               commands/does_not_exist
"""

sample_global_file = """
shared_folders:
    other_folder:
        folder:             invalid_folder
        mountpoint:         target_mountpoint
        parameters:
            edi_current_user_target_home_directory: /foo/bar

bootstrap:
    repository_key:     https://ftp-master.debian.org/keys/archive-key-8.asc

postprocessing_commands:
    20_second_step:
        path:               commands/command
        parameters:
            message:        "*second step* (not printed since no output specified)"
    30_third_step:
        path:               commands/skipped
        skip:               True
    40_fourth_step:
        path:               commands/command
        parameters:
            message:        "*last step*"
        require_root:       False
        output:             last.txt

"""

sample_system_file = """
shared_folders:
    other_folder:
        folder:             valid_folder
    skip_me:
        skip:               True

bootstrap:
    architecture:           i386

playbooks:
    30_foo:
        path:               playbooks/foo.yml
    40_bar:
        path:               playbooks/bar.yml
"""

sample_user_file = """
---
# apply no changes to bootstrap section

playbooks:
    10_base_system:
        parameters:
            kernel_package: linux-image-amd64-rt
    20_networking:
        path:               playbooks/foo.yml
    40_bar:
        skip: True
"""

sample_command = """#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail

INPUT_FILE="{{ edi_input_artifact }}"
OUTPUT_FILE="{{ edi_output_artifact }}"
MESSAGE="{{ message }}"

if [ "${INPUT_FILE}" == "" ]
then
    exit 1
fi

if [ "${OUTPUT_FILE}" == "" ]
then
    exit 0
fi

cp ${INPUT_FILE} ${OUTPUT_FILE}
echo "${MESSAGE}" >> ${OUTPUT_FILE}
"""

_config_name = "sample"
_empty_config_name = "empty"
_empty_overlay_config_name = "hugo"


@fixture(scope='function')
def config_name():
    return _config_name


@fixture(scope='function')
def config_files(tmpdir_factory):
    dir_name = tmpdir_factory.mktemp('configuration')
    main_file = "{0}.yml".format(_config_name)
    with open(str(dir_name.join(main_file)), "w") as file:
        file.write(sample_file)

    overlay_dir = dir_name.join("configuration", "overlay")
    os.makedirs(str(overlay_dir))
    overlays = [("global", sample_global_file),
                (get_user(), sample_user_file),
                (get_hostname(), sample_system_file)]
    for overlay in overlays:
        o_type, o_content = overlay
        o_file_name = "{0}.{1}.yml".format(_config_name, o_type)
        with open(str(overlay_dir.join(o_file_name)), "w") as o_file:
            o_file.write(o_content)

    playbook_dir = dir_name.join("plugins", "playbooks")
    os.makedirs(str(playbook_dir))
    with open(str(playbook_dir.join("foo.yml")), "w") as file:
        file.write("baz")

    commands_dir = dir_name.join("plugins", "commands")
    os.makedirs(str(commands_dir))

    with open(str(commands_dir.join("command")), "w") as file:
        file.write(sample_command)

    return str(dir_name.join(main_file))


@fixture(scope='function')
def empty_config_file(tmpdir_factory):
    dir_name = tmpdir_factory.mktemp('configuration')
    main_file = "{0}.yml".format(_empty_config_name)
    with open(str(dir_name.join(main_file)), "w") as file:
        file.write("")

    return str(dir_name.join(main_file))


@fixture(scope='function')
def empty_overlay_config_file(tmpdir_factory):
    dir_name = tmpdir_factory.mktemp('configuration')
    main_file = "{0}.yml".format(_empty_overlay_config_name)
    with open(str(dir_name.join(main_file)), "w") as file:
        file.write(sample_file)

    overlay_dir = dir_name.join("configuration", "overlay")
    os.makedirs(str(overlay_dir))
    overlays = [("global", "")]
    for overlay in overlays:
        o_type, o_content = overlay
        o_file_name = "{0}.{1}.yml".format(_empty_overlay_config_name, o_type)
        with open(str(overlay_dir.join(o_file_name)), "w") as o_file:
            o_file.write(o_content)

    return str(dir_name.join(main_file))
