# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
#
# Authors:
#  Matthias Luescher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.

import pytest
from edi.lib.helpers import get_user, get_hostname
from edi.lib.configurationparser import ConfigurationParser

sample_file = """
---
global_configuration:
    use_case:           edi_run
    compression:        gz

bootstrap_stage:
    architecture:       amd64
    repository:         deb http://ftp.ch.debian.org/debian/ jessie main

configuration_stage:
    - identifier:       Linux container
      playbook:         edi/plugins/lxc/lxc.yml
      parameters:
          edi_message:  Hello world!

    - identifier:       Minimal system
      playbook:         edi/plugins/minimal/minimal.yml
"""

sample_all_file = """
global_configuration:
    # change the use case:
    use_case:           edi_develop

bootstrap_stage:
    repository_key:     https://ftp-master.debian.org/keys/archive-key-8.asc
"""

sample_host_file = """
global_configuration:
    # change the use case:
    use_case:           edi_build

bootstrap_stage:
    architecture:       i386
"""

sample_user_file = """
---
global_configuration:
    # change the use case again:
    use_case:           edi_test

# apply no changes to the bootstrap stage

configuration_stage:
    # keep the element but change the message:
    - identifier:       Linux container
      parameters:
          edi_message:  Hello user!

    # keep the element without change:
    - identifier:       Minimal system
"""

config_name = "sample"


@pytest.fixture(scope='module')
def config_files(tmpdir_factory):
    dir_name = tmpdir_factory.mktemp('configuration')
    main_file = "{0}.yml".format(config_name)
    with open(str(dir_name.join(main_file)), "w") as file:
        file.write(sample_file)
    all_file = "{0}.{1}.yml".format(config_name, "all")
    with open(str(dir_name.join(all_file)), "w") as file:
        file.write(sample_all_file)
    user_file = "{0}.{1}.yml".format(config_name, get_user())
    with open(str(dir_name.join(user_file)), "w") as file:
        file.write(sample_user_file)
    host_file = "{0}.{1}.yml".format(config_name, get_hostname())
    with open(str(dir_name.join(host_file)), "w") as file:
        file.write(sample_host_file)
    return str(dir_name.join(main_file))


def test_project_name(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        assert parser.get_project_name() == config_name


def test_global_configuration_overlay(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        # the user file shall win:
        assert parser.get_use_case() == "edi_test"
        assert parser.get_compression() == "gz"


def test_bootstrap_stage_overlay(config_files):
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


def test_configuration_stage_overlay(config_files):
    # TODO
    pass
