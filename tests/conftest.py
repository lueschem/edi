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

import pytest
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
    parser.addoption("--flake8", action="store_true",
                     help="include tests that rely on flake8 availability")


def pytest_configure(config):
    config.addinivalue_line("markers", "requires_lxc: mark test as requiring lxc to run")
    config.addinivalue_line("markers", "requires_ansible: mark test as requiring ansible to run")
    config.addinivalue_line("markers", "requires_debootstrap: mark test as requiring debootstrap to run")
    config.addinivalue_line("markers", "requires_flake8: mark test as requiring flake8 to run")
    config.addinivalue_line("markers", "requires_sudo: mark test as requiring sudo to run")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "requires_lxc" in item.keywords and not (config.getoption("--lxc") or config.getoption("--all")):
            item.add_marker(pytest.mark.skip(reason="requires --lxc or --all option to run"))
        if "requires_ansible" in item.keywords and not (config.getoption("--ansible") or config.getoption("--all")):
            item.add_marker(pytest.mark.skip(reason="requires --ansible or --all option to run"))
        if "requires_debootstrap" in item.keywords and not (config.getoption("--debootstrap") or
                                                            config.getoption("--all")):
            item.add_marker(pytest.mark.skip(reason="requires --debootstrap or --all option to run"))
        if "requires_flake8" in item.keywords and not (config.getoption("--flake8") or config.getoption("--all")):
            item.add_marker(pytest.mark.skip(reason="requires --flake8 or --all option to run"))
        if "requires_sudo" in item.keywords and os.getuid() != 0:
            item.add_marker(pytest.mark.skip(reason="requires sudo privileges to run"))


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
    edi_lxc_stop_timeout:   130
    parameters:
        param1: keep
        param2: do_overwrite

qemu:
    package: qemu-user-static

shared_folders:
    skip_me:
        folder:             skip
        mountpoint:         me
    workspace:
        folder:             edi_marker_work
        mountpoint:         mywork

bootstrap:
    tool:                   debootstrap
    architecture:           amd64
    repository:             deb http://deb.debian.org/debian/ jessie main

lxc_templates:
    10_foo:
        path:              templates/foo.yml

lxc_profiles:
    10_foo:
        path:              profiles/foo.yml

playbooks:
    10_base_system:
        path:               playbooks/foo.yml
        parameters:
            kernel_package: linux-image-amd64
            message:        some message
            param3:         customized
    20_networking:
        path:               playbooks/bar.yml

postprocessing_commands:
    10_first_command:
        path:               commands/first
        output:
            first_output_file: first.txt
            first_output_folder: first_folder
        parameters:
            message:        "*first step*"
    20_second_command:
        path:               commands/does_not_exist
        output:
            second_output_file: overwrite_me.txt

documentation_steps:
    10_first_step:
        path:               documentation_steps/first.j2
        parameters:
            message:        "first step"
    20_second_step:
        path:               documentation_steps/second.j2
        parameters:
            edi_doc_include_packages: ['a','b','c']
    30_last_step:
        path:               path/to/last.j2
        skip:               True
        parameters:
            message:        "skipping first step"
"""

sample_global_file = """
general:
    parameters:
        param2: overwritten
        param3: new

shared_folders:
    other_folder:
        folder:             invalid_folder
        mountpoint:         target_mountpoint
        parameters:
            edi_current_user_target_home_directory: /foo/bar

bootstrap:
    repository_key:     https://ftp-master.debian.org/keys/archive-key-8.asc

postprocessing_commands:
    20_second_command:
        path:               commands/second
        parameters:
            message:        "*second step*"
        output:
            second_output_file: second.txt
    30_third_command:
        path:               commands/skipped
        skip:               True
        output:
            will_get_skipped: nothing.txt
    40_last_command:
        path:               commands/last
        parameters:
            message:        "*last step*"
        require_root:       False
        output:
            last_output_file: last.txt

documentation_steps:
    20_second_step:
        parameters:
            edi_doc_include_packages: ['x','y','z']
"""

sample_system_file = """
shared_folders:
    other_folder:
        folder:             edi_marker_valid_folder
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

first_command = """#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail

INPUT_FILE="{{ edi_input_artifact }}"
OUTPUT_FILE="{{ first_output_file }}"
OUTPUT_FOLDER="{{ first_output_folder }}"
MESSAGE="{{ message }}"

cp ${INPUT_FILE} ${OUTPUT_FILE}
echo "${MESSAGE}" >> ${OUTPUT_FILE}
mkdir "${OUTPUT_FOLDER}"
"""


second_command = """#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail

INPUT_FILE="{{ first_output_file }}"
OUTPUT_FILE="{{ second_output_file }}"
MESSAGE="{{ message }}"

cp ${INPUT_FILE} ${OUTPUT_FILE}
echo "${MESSAGE}" >> ${OUTPUT_FILE}
"""


last_command = """#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail

INPUT_FILE="{{ second_output_file }}"
OUTPUT_FILE="{{ last_output_file }}"
MESSAGE="{{ message }}"

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
    user = get_user()
    hostname = get_hostname()
    if user == hostname:
        user = '{}.user'.format(user)
    overlays = [("global", sample_global_file),
                (user, sample_user_file),
                (hostname, sample_system_file)]
    for overlay in overlays:
        o_type, o_content = overlay
        o_file_name = "{0}.{1}.yml".format(_config_name, o_type)
        with open(str(overlay_dir.join(o_file_name)), "w") as o_file:
            o_file.write(o_content)

    for subdir in ['playbooks', 'templates', 'profiles']:
        directory = dir_name.join("plugins", subdir)
        os.makedirs(str(directory))
        with open(str(directory.join("foo.yml")), "w") as file:
            file.write("baz")

    commands_dir = dir_name.join("plugins", "commands")
    os.makedirs(str(commands_dir))

    commands = [('first', first_command), ('second', second_command), ('last', last_command), ]
    for name, content in commands:
        with open(str(commands_dir.join(name)), "w") as file:
            file.write(content)

    documentation_steps_dir = dir_name.join("plugins", "documentation_steps")
    os.makedirs(str(documentation_steps_dir))

    steps = [('first.j2', 't1'), ('second.j2', 't2'), ]
    for name, content in steps:
        with open(str(documentation_steps_dir.join(name)), "w") as file:
            file.write(content)

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
