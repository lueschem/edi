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

from aptsources.sourceslist import SourceEntry
from edi.lib.configurationparser import ConfigurationParser
from tests.libtesting.fixtures.configfiles import config_files, config_name
import subprocess


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
        boostrap_source = SourceEntry(parser.get_bootstrap_repository())
        assert parser.get_bootstrap_architecture() == "i386"
        assert "main" in boostrap_source.comps
        assert boostrap_source.uri == "http://ftp.ch.debian.org/debian/"
        # the all file shall provide this key
        expected_key = "https://ftp-master.debian.org/keys/archive-key-8.asc"
        assert parser.get_bootstrap_repository_key() == expected_key
        assert boostrap_source.dist == "jessie"
        assert parser.get_bootstrap_tool() == "debootstrap"


def test_playbooks_overlay(config_files, monkeypatch):
    def fakerun(*popenargs, **kwargs):
        return subprocess.CompletedProcess("fakerun", 0, '')

    monkeypatch.setattr(subprocess, 'run', fakerun)

    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        playbooks = parser.get_ordered_path_items("playbooks")
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


def test_shared_folders(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        shared_folders = parser.get_ordered_raw_items('shared_folders')

        # first element
        name, content, dict = shared_folders[0]
        assert dict.get('edi_current_user_host_home_directory')
        assert name == 'other_folder'
        assert content.get('mountpoint') == 'target_mountpoint'
        assert content.get('folder') == 'valid_folder' # merge result

        # second element
        name, content, dict = shared_folders[1]
        assert name == 'workspace'
        assert content.get('mountpoint') == 'mywork'
        assert content.get('folder') == 'work'
