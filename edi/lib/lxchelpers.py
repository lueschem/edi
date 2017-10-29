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
from edi.lib.helpers import FatalError
from edi.lib.shellhelpers import run


def is_in_image_store(name):
    cmd = ["lxc", "image", "show", "local:{}".format(name)]
    result = run(cmd, check=False, stderr=subprocess.PIPE)
    return result.returncode == 0


def import_image(image, image_name):
    cmd = ["lxc", "image", "import", image, "local:", "--alias", image_name]
    run(cmd)


def export_image(image_name, image_without_extension):
    cmd = ["lxc", "image", "export", image_name, image_without_extension]
    run(cmd)


def publish_container(container_name, image_name):
    cmd = ["lxc", "publish", container_name, "--alias", image_name]
    run(cmd)


def delete_image(name):
    cmd = ["lxc", "image", "delete", "local:{}".format(name)]
    run(cmd)


def is_container_existing(name):
    cmd = ["lxc", "info", name]
    result = run(cmd, check=False, stderr=subprocess.PIPE)
    return result.returncode == 0


def is_container_running(name):
    cmd = ["lxc", "list", "--format=json", "^{}$".format(name)]
    result = run(cmd, stdout=subprocess.PIPE)

    try:
        parsed_result = yaml.load(result.stdout)
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


def launch_container(image, name, profiles):
    cmd = ["lxc", "launch", "local:{}".format(image), name]
    for profile in profiles:
        cmd.extend(["-p", profile])
    result = run(cmd, check=False, stderr=subprocess.PIPE, log_threshold=logging.INFO)
    if result.returncode != 0:
        if 'Missing parent' in result.stderr and 'lxdbr0' in result.stderr:
            raise FatalError(('''Launching image '{}' failed with the following message:\n{}'''
                              'Please make sure that lxdbr0 is available. Use one of the following commands to '
                              'create lxdbr0:\n'
                              'lxd init\n'
                              'or (for lxd >= 2.3)\n'
                              'lxc network create lxdbr0').format(image, result.stderr))
        else:
            raise FatalError(('''Launching image '{}' failed with the following message:\n{}'''
                              ).format(image, result.stderr))


def start_container(name):
    cmd = ["lxc", "start", name]

    run(cmd, log_threshold=logging.INFO)


def stop_container(name, timeout=120):
    cmd = ["lxc", "stop", name]

    try:
        run(cmd, log_threshold=logging.INFO, timeout=timeout)
    except subprocess.TimeoutExpired:
        logging.warning(("Timeout ({} seconds) expired while stopping container {}.\n"
                         "Forcing container shutdown!").format(timeout, name))
        cmd = ["lxc", "stop", "-f", name]
        run(cmd, log_threshold=logging.INFO)


def delete_container(name):
    # needs to be stopped first!
    cmd = ["lxc", "delete", name]

    run(cmd, log_threshold=logging.INFO)


def apply_profiles(name, profiles):
    cmd = ['lxc', 'profile', 'apply', name, ','.join(profiles)]
    run(cmd)


def is_profile_existing(name):
    cmd = ["lxc", "profile", "show", name]
    result = run(cmd, check=False, stderr=subprocess.PIPE)
    return result.returncode == 0


def write_lxc_profile(profile_text):
    new_profile = False
    profile_yaml = yaml.load(profile_text)
    profile_hash = hashlib.sha256(profile_text.encode()
                                  ).hexdigest()[:20]
    profile_name = profile_yaml.get("name", "anonymous")
    ext_profile_name = "{}_{}".format(profile_name,
                                      profile_hash)
    profile_yaml["name"] = ext_profile_name
    profile_content = yaml.dump(profile_yaml,
                                default_flow_style=False)

    if not is_profile_existing(ext_profile_name):
        create_cmd = ["lxc", "profile", "create", ext_profile_name]
        run(create_cmd)
        new_profile = True

    edit_cmd = ["lxc", "profile", "edit", ext_profile_name]
    run(edit_cmd, input=profile_content)

    return ext_profile_name, new_profile


def get_server_image_compression_algorithm():
    cmd = ['lxc', 'config', 'get', 'images.compression_algorithm']
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


def get_container_profiles(name):
    cmd = ['lxc', 'config', 'show', name]
    result = run(cmd, stdout=subprocess.PIPE)
    return yaml.load(result.stdout).get('profiles', [])


def get_lxd_version():
    cmd = ['lxd', '--version']
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not result.stdout:
        # recent lxd versions print the version to stderr!
        return result.stderr.strip('\n')
    else:
        return result.stdout.strip('\n')
