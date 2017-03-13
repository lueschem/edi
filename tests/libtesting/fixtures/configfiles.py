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

import pytest
import os
from edi.lib.helpers import get_user, get_hostname

sample_file = """
---
general:
    edi_use_case:           edi_uc_run
    edi_compression:        gz

shared_folders:
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
"""

sample_global_file = """
general:
    # change the use case:
    edi_use_case:           edi_uc_develop

shared_folders:
    other_folder:
        folder:             invalid_folder
        mountpoint:         target_mountpoint
        parameters:
            edi_current_user_target_home_directory: /foo/bar

bootstrap:
    repository_key:     https://ftp-master.debian.org/keys/archive-key-8.asc
"""

sample_system_file = """
general:
    # change the use case:
    edi_use_case:           edi_uc_build

shared_folders:
    other_folder:
        folder:             valid_folder

bootstrap:
    architecture:           i386

playbooks:
    30_foo:
        path:               playbooks/foo.yml
"""

sample_user_file = """
---
general:
    # change the use case again:
    edi_use_case:           edi_uc_test

# apply no changes to bootstrap section

playbooks:
    10_base_system:
        parameters:
            kernel_package: linux-image-amd64-rt
    20_networking:
        path:               playbooks/foo.yml
"""

config_name = "sample"
empty_config_name = "empty"


@pytest.fixture(scope='function')
def config_files(tmpdir_factory):
    dir_name = tmpdir_factory.mktemp('configuration')
    main_file = "{0}.yml".format(config_name)
    with open(str(dir_name.join(main_file)), "w") as file:
        file.write(sample_file)

    overlay_dir = dir_name.join("configuration", "overlay")
    os.makedirs(str(overlay_dir))
    overlays = [("global", sample_global_file),
                (get_user(), sample_user_file),
                (get_hostname(), sample_system_file)]
    for overlay in overlays:
        o_type, o_content = overlay
        o_file_name = "{0}.{1}.yml".format(config_name, o_type)
        with open(str(overlay_dir.join(o_file_name)), "w") as o_file:
            o_file.write(o_content)

    playbook_dir = dir_name.join("plugins", "playbooks")
    os.makedirs(str(playbook_dir))
    with open(str(playbook_dir.join("foo.yml")), "w") as file:
        file.write("baz")
    return str(dir_name.join(main_file))


@pytest.fixture(scope='function')
def empty_config_file(tmpdir_factory):
    dir_name = tmpdir_factory.mktemp('configuration')
    main_file = "{0}.yml".format(empty_config_name)
    with open(str(dir_name.join(main_file)), "w") as file:
        file.write("general:")

    return str(dir_name.join(main_file))
