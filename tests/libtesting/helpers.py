# -*- coding: utf-8 -*-
# Copyright (C) 2017 Matthias Luescher
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

import os
import string
import random
import shutil
from edi.lib.helpers import get_user
from edi.lib import mockablerun


def get_random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def get_command(popenargs):
    def get_real_command(cmd, expected_position):
        if cmd[expected_position] == 'env':
            return cmd[expected_position + 2]
        else:
            return cmd[expected_position]

    command = popenargs[0]
    if command[0] == 'sudo':
        if command[1] == '-u':
            return get_real_command(command, 3)
        else:
            return get_real_command(command, 1)
    else:
        return get_real_command(command, 0)


def get_sub_command(popenargs):
    main_command = get_command(popenargs)
    return get_command_parameter(popenargs, main_command)


def get_command_parameter(popenargs, option):
    option_index = popenargs[0].index(option)
    return popenargs[0][option_index + 1]


def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def suppress_chown_during_debuild(monkeypatch):
    def fakechown(*_):
        pass

    if get_user() == 'root':  # debuild case
        monkeypatch.setattr(shutil, 'chown', fakechown)


def log_during_run(monkeypatch, do_log):
    def force_logging(*_):
        return do_log

    monkeypatch.setattr(mockablerun, 'is_logging_enabled_for', force_logging)
