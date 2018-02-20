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


from edi.lib.urlhelpers import obfuscate_url_password


def test_render_url():
    url_with_password = "http://user:password@example.com:3128"

    assert obfuscate_url_password(url_with_password) == "http://user:***@example.com:3128"

    url_without_password = "http://user@example.com:3128"
    assert obfuscate_url_password(url_without_password) == url_without_password
