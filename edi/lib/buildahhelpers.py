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

import subprocess
import yaml
import os
import logging
from packaging.version import Version
from edi.lib.helpers import FatalError
from edi.lib.versionhelpers import get_stripped_version
from edi.lib.shellhelpers import run, Executables, require


buildah_install_hint = "'sudo apt install buildah'"


def buildah_exec():
    return Executables.get('buildah')


def get_buildah_version():
    if not Executables.has('buildah'):
        return '0.0.0'

    cmd = [Executables.get("buildah"), "version", "--json"]
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    parsed_result = yaml.safe_load(result.stdout)
    return parsed_result.get('version')


class BuildahVersion:
    """
    Make sure that the buildah version is >= 1.23.1.
    """
    _check_done = False
    _required_minimal_version = '1.23.1'

    def __init__(self, clear_cache=False):
        if clear_cache:
            BuildahVersion._check_done = False

    @staticmethod
    def check():
        if BuildahVersion._check_done:
            return

        if Version(get_stripped_version(get_buildah_version())) < Version(BuildahVersion._required_minimal_version):
            raise FatalError(('The current buildah installation ({}) does not meet the minimal requirements (>={}).\n'
                              'Please update your buildah installation!'
                              ).format(get_buildah_version(), BuildahVersion._required_minimal_version))
        else:
            BuildahVersion._check_done = True


@require('buildah', buildah_install_hint, BuildahVersion.check)
def is_container_existing(name):
    cmd = [buildah_exec(), "inspect", name]
    result = run(cmd, check=False, stderr=subprocess.PIPE)
    return result.returncode == 0


@require('buildah', buildah_install_hint, BuildahVersion.check)
def delete_container(name):
    # needs to be stopped first!
    cmd = [buildah_exec(), "rm", name]

    run(cmd, log_threshold=logging.INFO)


@require('buildah', buildah_install_hint, BuildahVersion.check)
def create_container(name, rootfs_file):
    if is_container_existing(name):
        raise FatalError(f"The container '{name}' already exists!")

    if not os.path.isfile(rootfs_file):
        raise FatalError(f"The root file system archive '{rootfs_file}' does not exist!")

    temp_container_name = name + "-temp"

    if is_container_existing(temp_container_name):
        delete_container(temp_container_name)

    cmd = [buildah_exec(), "--name", temp_container_name, "from", "scratch"]
    run(cmd, log_threshold=logging.INFO)

    extract_command = "tar --numeric-owner --exclude=./dev -C " + r'${container_root}' + " -axf " + str(rootfs_file)

    run_buildah_unshare(temp_container_name, extract_command)

    cmd = [buildah_exec(), "rename", temp_container_name, name]
    run(cmd, log_threshold=logging.INFO)


@require('buildah', buildah_install_hint, BuildahVersion.check)
def run_buildah_unshare(name, command):
    cmd = [buildah_exec(), "unshare", "--mount", f"container_root={name}", "--", "bash", "-c", command]
    return run(cmd, log_threshold=logging.INFO)
