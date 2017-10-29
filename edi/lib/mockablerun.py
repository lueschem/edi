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


def run_mockable(*popenargs, **kwargs):
    """
    This pass through method allows to selectively intercept edi.lib.shellhelpers.run() commands.
    :param popenargs: pass through to subprocess.run
    :param kwargs: pass through to subprocess.run
    :return: passes back the result of subprocess.run()
    """
    return subprocess.run(*popenargs, **kwargs)
