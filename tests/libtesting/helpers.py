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


def get_command(popenargs):
    command = popenargs[0]
    if command[0] == 'sudo':
        if command[1] == '-u':
            return command[3]
        else:
            return command[1]
    else:
        return command[0]


def get_sub_command(popenargs):
    main_command = get_command(popenargs)
    return get_command_parameter(popenargs, main_command)


def get_command_parameter(popenargs, option):
    option_index = popenargs[0].index(option)
    return popenargs[0][option_index + 1]
