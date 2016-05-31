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
from edi.lib.configurationparser import ConfigurationParser

sample_file = """
---
general:
    edi_use_case:           edi_uc_run
    edi_compression:        gz

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

bootstrap:
    repository_key:     https://ftp-master.debian.org/keys/archive-key-8.asc
"""

sample_system_file = """
general:
    # change the use case:
    edi_use_case:           edi_uc_build

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


@pytest.fixture(scope='module')
def config_files(tmpdir_factory):
    dir_name = tmpdir_factory.mktemp('configuration')
    main_file = "{0}.yml".format(config_name)
    with open(str(dir_name.join(main_file)), "w") as file:
        file.write(sample_file)
    global_file = "{0}.{1}.yml".format(config_name, "global")
    with open(str(dir_name.join(global_file)), "w") as file:
        file.write(sample_global_file)
    user_file = "{0}.{1}.yml".format(config_name, get_user())
    with open(str(dir_name.join(user_file)), "w") as file:
        file.write(sample_user_file)
    host_file = "{0}.{1}.yml".format(config_name, get_hostname())
    with open(str(dir_name.join(host_file)), "w") as file:
        file.write(sample_system_file)
    playbook_dir = dir_name.join("plugins/playbooks")
    os.makedirs(str(playbook_dir))
    with open(str(playbook_dir.join("foo.yml")), "w") as file:
        file.write("baz")
    return str(dir_name.join(main_file))


def test_project_name(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        assert parser.get_project_name() == config_name


def test_global_configuration_overlay(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        # the user file shall win:
        assert parser.get_use_case() == "edi_uc_test"
        assert parser.get_compression() == "gz"


def test_bootstrap_overlay(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        # the host file shall win
        assert parser.get_architecture() == "i386"
        assert "main" in parser.get_bootstrap_components()
        assert parser.get_bootstrap_uri() == "http://ftp.ch.debian.org/debian/"
        # the all file shall provide this key
        expected_key = "https://ftp-master.debian.org/keys/archive-key-8.asc"
        assert parser.get_bootstrap_repository_key() == expected_key
        assert parser.get_distribution() == "jessie"
        assert parser.get_bootstrap_tool() == "debootstrap"


def test_playbooks_overlay(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        playbooks = parser.get_playbooks("edi_env_baremetal")
        assert len(playbooks) == 3
        expected_playbooks = ["10_base_system",
                              "20_networking",
                              "30_foo"]
        for playbook, expected in zip(playbooks, expected_playbooks):
            name, path, extra_vars = playbook
            assert name == expected
            if name == "10_base_system":
                value = extra_vars.get("kernel_package")
                assert value == "linux-image-amd64-rt"
                value = extra_vars.get("message")
                assert value == "some message"
            if name == "20_networking":
                assert path.endswith("playbooks/foo.yml")
