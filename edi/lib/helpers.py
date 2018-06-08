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

import sys
import os
from pwd import getpwnam
import socket
import logging
import shutil


class Error(Exception):
    """Base class for edi exceptions."""
    pass


class FatalError(Error):
    """Exception raised for fatal errors needing corrective actions from user.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


def print_error_and_exit(*args, **kwargs):
    print('\033[91m', end="", file=sys.stderr)
    print('Error: ', end="", file=sys.stderr)
    print(*args, end="", file=sys.stderr, **kwargs)
    print('\033[0m', file=sys.stderr)
    sys.exit(1)


def print_success(*args, **kwargs):
    print('\033[92m', end="")
    print('Success: ', end="")
    print(*args, end="", **kwargs)
    print('\033[0m')


def get_user():
    try:
        if 'SUDO_USER' in os.environ:
            return os.environ['SUDO_USER']
        else:
            return os.environ['USER']
    except KeyError:
        # Hint: there is no $USER during debuild
        logging.warning("Unable to get user from environment variable.")
        return "root"


def get_user_uid():
    return getpwnam(get_user()).pw_uid


def get_user_gid():
    return getpwnam(get_user()).pw_gid


def get_hostname():
    return socket.gethostname()


def get_edi_plugin_directory():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))


def copy_tree(src, dst):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.islink(s):
            linkto = os.readlink(s)
            os.symlink(linkto, d)
        elif os.path.isdir(s):
            shutil.copytree(s, d, symlinks=True)
        else:
            shutil.copy2(s, d)

    return dst


def which(executable):
    def is_exe(abs_path):
        return os.path.isfile(abs_path) and os.access(abs_path, os.X_OK)

    exe_dir, _ = os.path.split(executable)
    if exe_dir:
        if is_exe(executable):
            return executable
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file_path = os.path.join(path, executable)
            if is_exe(exe_file_path):
                return exe_file_path

    return None


def chown_to_user(path):
    shutil.chown(path, get_user_uid(), get_user_gid())


def get_workdir():
    return os.getcwd()


def get_artifact_dir():
    return os.path.join(get_workdir(), 'artifacts')


def create_artifact_dir():
    directory = get_artifact_dir()
    if not os.path.isdir(directory):
        logging.info('''Creating artifact directory '{}'.'''.format(directory))
        os.mkdir(directory)
        chown_to_user(directory)
