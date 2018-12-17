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

import re

_hostname_regexp = (r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*'
                    r'[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9]'
                    r'[A-Za-z0-9\-]*[A-Za-z0-9])$')


def is_valid_hostname(name):
    if re.match(_hostname_regexp, name) is None:
        return False
    else:
        return True
