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
import shutil
from contextlib import contextmanager
from edi.lib.helpers import get_user

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

    if not sudo:
        myargs = ["sudo", "-u", get_user()] + myargs
    elif sudo and os.getuid() != 0:
        myargs.insert(0, "sudo")

    logging.info("Running command: {0}".format(myargs))

    result = subprocess.run(myargs, input=input, timeout=timeout, check=check,
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
