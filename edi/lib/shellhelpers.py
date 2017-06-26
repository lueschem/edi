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
from edi.lib.helpers import get_user
from edi.lib import mockablerun

_ADAPTIVE = -42


def run(popenargs, sudo=False, input=None, timeout=None,
        check=True, universal_newlines=True, stdout=_ADAPTIVE,
        **kwargs):
    """
    Small wrapper around subprocess.run().
    """

    assert type(popenargs) is list

    subprocess_stdout = stdout

    if subprocess_stdout == _ADAPTIVE:
        if logging.getLogger().isEnabledFor(logging.INFO):
            subprocess_stdout = None
        else:
            subprocess_stdout = subprocess.PIPE

    myargs = popenargs.copy()

    if not sudo and os.getuid() == 0:
        current_user = get_user()
        if current_user != 'root':
            # drop privileges
            myargs = ["sudo", "-u", current_user] + myargs
    elif sudo and os.getuid() != 0:
        myargs.insert(0, "sudo")

    logging.info("Running command: {0}".format(myargs))

    result = mockablerun.run_mockable(myargs, input=input, timeout=timeout, check=check,
                                      universal_newlines=universal_newlines,
                                      stdout=subprocess_stdout, **kwargs)

    if (logging.getLogger().isEnabledFor(logging.INFO) and
            subprocess_stdout is subprocess.PIPE):
        logging.info(result.stdout)

    return result


def get_chroot_cmd(rootfs):
    cmd = []
    cmd.append("chroot")
    cmd.append(rootfs)
    return cmd


def get_user_environment_variable(name, default=None):
    # get the variable from the user, not from root if edi is called using sudo
    cmd = ["printenv", name]
    result = run(cmd, stdout=subprocess.PIPE, check=False)
    if result.returncode == 0:
        return result.stdout.strip('\n')
    else:
        return default


def get_debian_architecture():
    cmd = ['dpkg', '--print-architecture']
    return run(cmd, stdout=subprocess.PIPE).stdout.strip('\n')


def get_lxd_version():
    cmd = ['lxd', '--version']
    return run(cmd, stdout=subprocess.PIPE).stdout.strip('\n')