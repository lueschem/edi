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

import subprocess
import yaml
import logging
import hashlib
from packaging.version import Version
from edi.lib.helpers import FatalError
from edi.lib.versionhelpers import get_stripped_version
from edi.lib.shellhelpers import run, Executables, require


lxd_install_hint = "'sudo apt install lxd' or 'sudo snap install lxd'"


def lxc_exec():
    return Executables.get('lxc')


def get_lxd_version():
    if not Executables.has('lxd'):
        return '0.0.0'

    cmd = [Executables.get('lxd'), '--version']
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not result.stdout:
        # recent lxd versions print the version to stderr!
        return result.stderr.strip('\n')
    else:
        return result.stdout.strip('\n')


class LxdVersion:
    """
    Make sure that the lxc/lxd version is >= 3.0.0.
    """
    _check_done = False
    _required_minimal_version = '3.0.0'

    def __init__(self, clear_cache=False):
        if clear_cache:
            LxdVersion._check_done = False

    @staticmethod
    def check():
        if LxdVersion._check_done:
            return

        if Version(get_stripped_version(get_lxd_version())) < Version(LxdVersion._required_minimal_version):
            raise FatalError(('The current lxd installation ({}) does not meet the minimal requirements (>={}).\n'
                              'Please update your lxd installation using snaps or xenial-backports!'
                              ).format(get_lxd_version(), LxdVersion._required_minimal_version))
        else:
            LxdVersion._check_done = True


@require('lxc', lxd_install_hint, LxdVersion.check)
def is_in_image_store(name):
    cmd = [lxc_exec(), "image", "show", "local:{}".format(name)]
    result = run(cmd, check=False, stderr=subprocess.PIPE)
    return result.returncode == 0


@require('lxc', lxd_install_hint, LxdVersion.check)
def import_image(image, image_name):
    cmd = [lxc_exec(), "image", "import", image, "local:", "--alias", image_name]
    run(cmd)


@require('lxc', lxd_install_hint, LxdVersion.check)
def export_image(image_name, image_without_extension):
    cmd = [lxc_exec(), "image", "export", image_name, image_without_extension]
    run(cmd)


@require('lxc', lxd_install_hint, LxdVersion.check)
def publish_container(container_name, image_name):
    cmd = [lxc_exec(), "publish", container_name, "--alias", image_name]
    run(cmd)


@require('lxc', lxd_install_hint, LxdVersion.check)
def delete_image(name):
    cmd = [lxc_exec(), "image", "delete", "local:{}".format(name)]
    run(cmd)


@require('lxc', lxd_install_hint, LxdVersion.check)
def is_container_existing(name):
    cmd = [lxc_exec(), "info", name]
    result = run(cmd, check=False, stderr=subprocess.PIPE)
    return result.returncode == 0


@require('lxc', lxd_install_hint, LxdVersion.check)
def is_container_running(name):
    cmd = [lxc_exec(), "list", "--format=json", "^{}$".format(name)]
    result = run(cmd, stdout=subprocess.PIPE)

    try:
        parsed_result = yaml.safe_load(result.stdout)
        if len(parsed_result) != 1:
            return False
        else:
            status = parsed_result[0].get("status", "")
            if status == "Running":
                return True
            else:
                return False
    except yaml.YAMLError as exc:
        raise FatalError("Unable to parse lxc output ({}).".format(exc))


@require('lxc', lxd_install_hint, LxdVersion.check)
def is_bridge_available(bridge_name):
    cmd = [lxc_exec(), "network", "list", "--format=json"]
    result = run(cmd, stdout=subprocess.PIPE)

    try:
        parsed_result = yaml.safe_load(result.stdout)
        bridge_names = [item.get("name") for item in parsed_result]
        if bridge_name in bridge_names:
            return True
        else:
            return False
    except yaml.YAMLError as exc:
        raise FatalError("Unable to parse lxc output ({}).".format(exc))


@require('lxc', lxd_install_hint, LxdVersion.check)
def create_bridge(bridge_name):
    cmd = [lxc_exec(), "network", "create", bridge_name]
    run(cmd)


@require('lxc', lxd_install_hint, LxdVersion.check)
def launch_container(image, name, profiles):
    cmd = [lxc_exec(), "launch", "local:{}".format(image), name]
    for profile in profiles:
        cmd.extend(["-p", profile])
    result = run(cmd, check=False, stderr=subprocess.PIPE, log_threshold=logging.INFO)
    if result.returncode != 0:
        raise FatalError(('''Launching image '{}' failed with the following message:\n{}'''
                          ).format(image, result.stderr))


@require('lxc', lxd_install_hint, LxdVersion.check)
def start_container(name):
    cmd = [lxc_exec(), "start", name]

    run(cmd, log_threshold=logging.INFO)


@require('lxc', lxd_install_hint, LxdVersion.check)
def stop_container(name, timeout=120):
    cmd = [lxc_exec(), "stop", name]

    try:
        run(cmd, log_threshold=logging.INFO, timeout=timeout)
    except subprocess.TimeoutExpired:
        logging.warning(("Timeout ({} seconds) expired while stopping container {}.\n"
                         "Forcing container shutdown!").format(timeout, name))
        cmd = [lxc_exec(), "stop", "-f", name]
        run(cmd, log_threshold=logging.INFO)


@require('lxc', lxd_install_hint, LxdVersion.check)
def delete_container(name):
    # needs to be stopped first!
    cmd = [lxc_exec(), "delete", name]

    run(cmd, log_threshold=logging.INFO)


@require('lxc', lxd_install_hint, LxdVersion.check)
def apply_profiles(name, profiles):
    cmd = [lxc_exec(), 'profile', 'apply', name, ','.join(profiles)]
    run(cmd)


@require('lxc', lxd_install_hint, LxdVersion.check)
def is_profile_existing(name):
    cmd = [lxc_exec(), "profile", "show", name]
    result = run(cmd, check=False, stderr=subprocess.PIPE)
    return result.returncode == 0


@require('lxc', lxd_install_hint, LxdVersion.check)
def write_lxc_profile(profile_text):
    new_profile = False
    profile_yaml = yaml.safe_load(profile_text)
    profile_hash = hashlib.sha256(profile_text.encode()
                                  ).hexdigest()[:20]
    profile_name = profile_yaml.get("name", "anonymous")
    ext_profile_name = "{}_{}".format(profile_name,
                                      profile_hash)
    profile_yaml["name"] = ext_profile_name
    profile_content = yaml.dump(profile_yaml,
                                default_flow_style=False)

    if not is_profile_existing(ext_profile_name):
        create_cmd = [lxc_exec(), "profile", "create", ext_profile_name]
        run(create_cmd)
        new_profile = True

    edit_cmd = [lxc_exec(), "profile", "edit", ext_profile_name]
    run(edit_cmd, input=profile_content)

    return ext_profile_name, new_profile


@require('lxc', lxd_install_hint, LxdVersion.check)
def get_server_image_compression_algorithm():
    cmd = [lxc_exec(), 'config', 'get', 'images.compression_algorithm']
    algorithm = run(cmd, stdout=subprocess.PIPE).stdout.strip('\n')
    if not algorithm:
        return 'gzip'
    else:
        return algorithm


def get_file_extension_from_image_compression_algorithm(algorithm):
    mapping = {
        'bzip2': '.tar.bz2',
        'gzip': '.tar.gz',
        'lzma': '.tar.lzma',
        'xz': '.tar.xz',
        'none': '.tar',
    }

    extension = mapping.get(algorithm, None)
    if not extension:
        raise FatalError(('''Unhandled lxc image compression algorithm '{}'.'''
                          ).format(algorithm))

    return extension


@require('lxc', lxd_install_hint, LxdVersion.check)
def get_container_profiles(name):
    cmd = [lxc_exec(), 'config', 'show', name]
    result = run(cmd, stdout=subprocess.PIPE)
    return yaml.safe_load(result.stdout).get('profiles', [])


def try_delete_container(container_name, timeout):
    """
    Try to delete a container.
    :param container_name: The name of the container.
    :param timeout: Stop timeout in seconds.
    :return: True if container got deleted, False if container does not exist.
    """
    if is_container_existing(container_name):
        if is_container_running(container_name):
            stop_container(container_name, timeout=timeout)

        delete_container(container_name)
        return True
    else:
        return False
