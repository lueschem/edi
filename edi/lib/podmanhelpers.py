# -*- coding: utf-8 -*-
# Copyright (C) 2024 Matthias Luescher
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

import subprocess
import yaml
import logging
from packaging.version import Version
from edi.lib.helpers import FatalError
from edi.lib.versionhelpers import get_stripped_version
from edi.lib.shellhelpers import run, Executables, require


podman_install_hint = "'sudo apt install podman'"


def podman_exec():
    return Executables.get('podman')


def get_podman_version():
    if not Executables.has('podman'):
        return '0.0.0'

    cmd = [Executables.get("podman"), "version", "--format=json"]
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    parsed_result = yaml.safe_load(result.stdout)
    return parsed_result.get('Client').get('Version')


class PodmanVersion:
    """
    Make sure that the podman version is >= 4.3.1.
    """
    _check_done = False
    _required_minimal_version = '4.3.1'

    def __init__(self, clear_cache=False):
        if clear_cache:
            PodmanVersion._check_done = False

    @staticmethod
    def check():
        if PodmanVersion._check_done:
            return

        if Version(get_stripped_version(get_podman_version())) < Version(PodmanVersion._required_minimal_version):
            raise FatalError(('The current podman installation ({}) does not meet the minimal requirements (>={}).\n'
                              'Please update your podman installation!'
                              ).format(get_podman_version(), PodmanVersion._required_minimal_version))
        else:
            PodmanVersion._check_done = True


@require('podman', podman_install_hint, PodmanVersion.check)
def is_image_existing(name, sudo=False):
    cmd = [podman_exec(), "image", "exists", name]
    result = run(cmd, check=False, stderr=subprocess.PIPE, sudo=sudo)
    return result.returncode == 0


@require('podman', podman_install_hint, PodmanVersion.check)
def try_delete_image(name, sudo=False):
    cmd = [podman_exec(), "image", "rm", name]
    result = run(cmd, check=False, stderr=subprocess.PIPE, sudo=sudo)
    return result.returncode == 0


@require('podman', podman_install_hint, PodmanVersion.check)
def untag_image(name, sudo=False):
    cmd = [podman_exec(), "image", "untag", name]
    run(cmd, log_threshold=logging.INFO, sudo=sudo)
