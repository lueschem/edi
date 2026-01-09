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

import logging
import subprocess
import os
import re
from pwd import getpwuid
from shutil import rmtree
from tempfile import mkdtemp
from contextlib import contextmanager
from edi.lib.helpers import get_user, get_artifact_dir, FatalError, which
from edi.lib import mockablerun

_ADAPTIVE = -42


def run(popenargs, sudo=False, input=None, timeout=None, check=True, universal_newlines=True,
        stdout=_ADAPTIVE, log_threshold=logging.DEBUG,
        **kwargs):
    """
    Small wrapper around subprocess.run().
    """

    assert type(popenargs) is list

    subprocess_stdout = stdout

    if subprocess_stdout == _ADAPTIVE:
        if mockablerun.is_logging_enabled_for(log_threshold):
            subprocess_stdout = None
        else:
            subprocess_stdout = subprocess.PIPE

    all_args = list()
    if not sudo and os.getuid() == 0 and not is_running_in_user_namespace():
        current_user = get_user()
        if current_user != 'root':
            # drop privileges
            all_args.extend(['sudo', '-u', current_user])
    elif sudo and os.getuid() != 0:
        all_args.append('sudo')

    all_args.extend(popenargs)

    logging.log(log_threshold, "Running command: {0}".format(all_args))

    result = mockablerun.run_mockable(all_args, input=input, timeout=timeout, check=check,
                                      universal_newlines=universal_newlines,
                                      stdout=subprocess_stdout, **kwargs)

    if (mockablerun.is_logging_enabled_for(log_threshold) and
            subprocess_stdout is subprocess.PIPE):
        logging.log(log_threshold, result.stdout)

    return result


def is_running_in_user_namespace():
    return getpwuid(os.stat(os.path.join(os.sep, 'etc', 'sudoers')).st_uid).pw_name == "nobody"


def get_chroot_cmd(rootfs):
    cmd = []
    cmd.append("chroot")
    cmd.append(rootfs)
    return cmd


def get_environment_variable(name, default=None):
    # the environment variable HOME is treated differently on Ubuntu and Debian
    # use get_user_home_directory instead
    assert name != 'HOME'
    cmd = ["printenv", name]
    # in order to keep environment variables do not drop privileges with sudo -u ...
    keep_sudo = os.getuid() == 0
    result = run(cmd, stdout=subprocess.PIPE, check=False, sudo=keep_sudo)
    if result.returncode == 0:
        return result.stdout.strip('\n')
    else:
        return default


def get_current_display():
    display_variable = get_environment_variable('DISPLAY', '')
    display_no, substitutions = re.subn(r'^.*:([0-9]*)[.]?[0-9]*$', r'\1', display_variable)
    if substitutions == 1:
        return display_no
    else:
        return ''


def get_user_home_directory(username):
    cmd = ['getent', 'passwd', username]
    result = run(cmd, stdout=subprocess.PIPE)
    return result.stdout.split(':')[5]


def get_debian_architecture():
    cmd = ['dpkg', '--print-architecture']
    return run(cmd, stdout=subprocess.PIPE).stdout.strip('\n')


def safely_remove_artifacts_folder(abs_folder_path, sudo=False):
    """
    Do some paranoid checking before removing a folder possibly using sudo.
    :param abs_folder_path: Absolute path to folder that should get deleted.
    :param sudo: If True, use sudo to delete folder.
    """
    artifacts_dir = get_artifact_dir()
    assert 'artifacts' in str(abs_folder_path)
    assert str(artifacts_dir) in str(abs_folder_path)
    assert os.path.isdir(abs_folder_path)
    assert os.path.isabs(abs_folder_path)
    mount_result = run(['mount'], stdout=subprocess.PIPE)
    if str(abs_folder_path) in mount_result.stdout:
        raise FatalError(('''Refusing to delete '{}' since it contains mounted elements.'''
                          ).format(abs_folder_path))
    run(['rm', '-rf', abs_folder_path], sudo=sudo)


@contextmanager
def mount_aware_tempdir(parent_dir, log_warning=False):
    directory = mkdtemp(dir=parent_dir)
    assert str(parent_dir) in str(directory)
    try:
        yield directory
    finally:
        mount_points = run(['findmnt', '--noheadings', '--raw', '--output=target'], stdout=subprocess.PIPE)
        for mount_point in mount_points.stdout.splitlines():
            if str(parent_dir) in mount_point:
                if log_warning:
                    logging.warning("Going to unmount '{}'.".format(mount_point))
                run(['umount', mount_point], sudo=True)
        rmtree(directory)


@contextmanager
def gpg_agent(directory):
    """
    gpg >= 2.1 will automatically launch a gpg agent that creates some unix sockets.
    tempfile.TemporaryDirectory will fail to remove those unix sockets. Therefore this contextmanager will take
    care of the socket removal.
    Please note that the removal of the sockets will trigger the shutdown of the respective gpg-agent.
    :param directory: The directory where the sockets are located.
    """
    try:
        yield
    finally:
        for file in os.listdir(directory):
            if file.startswith('S.gpg-agent'):
                try:
                    os.remove(os.path.join(directory, file))
                except OSError:
                    pass


class Executables:
    """
    Caches the availability of executables.
    """
    _cache = dict()

    def __init__(self, clear_cache=False):
        if clear_cache:
            Executables._cache = dict()

    @staticmethod
    def has(executable):
        if executable in Executables._cache:
            return bool(Executables._cache.get(executable))
        else:
            result = which(executable)
            Executables._cache[executable] = result
            return bool(result)

    @classmethod
    def get(cls, executable):
        """
        Get the absolute path to an executable.
        :param executable: name of the executable
        :return: /path/to/executable or None
        """
        if cls.has(executable):
            return Executables._cache[executable]
        else:
            return None


def require(executable, installation_command=None, version_check=None):
    """
    Make sure that a certain executable is available.
    Use this method as a decorator.
    :param executable: The required executable.
    :param installation_command: A suggested installation command if the executable is missing.
    :param version_check: A method to check the installed executable (e.g. required minimal version).
    :return:
    """
    def require_decorator(func):
        def func_wrapper(*args, **kwargs):
            if not Executables.has(executable):
                if not installation_command:
                    installation_hint = 'apt or snap'
                else:
                    installation_hint = installation_command
                raise FatalError(("Missing executable '{0}'.\n"
                                  "Use e.g. {1} to install it.").format(executable,
                                                                        installation_hint))
            elif version_check:
                version_check()

            return func(*args, **kwargs)

        return func_wrapper

    return require_decorator
