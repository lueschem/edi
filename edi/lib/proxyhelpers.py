# -*- coding: utf-8 -*-
# Copyright (C) 2018 Matthias Luescher
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


from edi.lib.shellhelpers import get_user_environment_variable


def get_proxy_setup(protocol):
    protocol_to_env = {
        'http': 'http_proxy',
        'https': 'https_proxy',
        'ftp': 'ftp_proxy',
        'socks': 'all_proxy',
        'no': 'no_proxy'
    }
    assert protocol in protocol_to_env.keys()

    result = get_user_environment_variable(protocol_to_env[protocol], default='')

    return result