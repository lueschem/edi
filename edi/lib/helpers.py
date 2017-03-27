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
import pkg_resources
import re
from packaging.version import Version


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
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(executable)
    if fpath:
        if is_exe(executable):
            return executable
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file_path = os.path.join(path, executable)
            if is_exe(exe_file_path):
                return exe_file_path

    return None


def require_executable(executable, hint):
    if which(executable) is None:
        raise FatalError(("Missing executable '{0}'.\n"
                          "Use '{1}' to install it.").format(executable,
                                                             hint))


def chown_to_user(path):
    shutil.chown(path, get_user_uid(), get_user_gid())


def get_edi_version_string():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    git_dir = os.path.join(project_root, ".git")
    if os.path.isdir(git_dir):
        # do import locally so that we do not depend on setuptools_scm for the released version
        from setuptools_scm import get_version
        return get_version(root=project_root)
    else:
        return pkg_resources.get_distribution('edi').version


def parse_version(version_string):
    """
    Strips the suffixes from the version string and returns a PEP 440 compliant version object.

    :param version_string: String that needs to be parsed
    :return: packaging.version.Version(MAJOR.MINOR.PATCH)
    """
    result = re.match('\d+(\.\d+){0,2}', version_string)
    if result:
        version_string = result.group(0)
    else:
        raise FatalError('''Unable to parse version string '{}'.'''.format(version_string))

    return Version(version_string)
