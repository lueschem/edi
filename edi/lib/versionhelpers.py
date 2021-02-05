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
import pkg_resources
import re
from edi.lib.helpers import FatalError

# The do_release script will update this version!
# During launchpad debuild neither the git version nor the package version is available.
edi_fallback_version = '1.9.0'


def get_edi_version():
    """
    Get the version of the current edi installation or the version derived from git.

    :return: full edi version string
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    git_dir = os.path.join(project_root, ".git")
    if os.path.isdir(git_dir):
        # do import locally so that we do not depend on setuptools_scm for the released version
        from setuptools_scm import get_version
        return get_version(root=project_root)
    else:
        try:
            return pkg_resources.get_distribution('edi').version
        except pkg_resources.DistributionNotFound:
            return edi_fallback_version


def get_stripped_version(version):
    """
    Strips the suffixes from the version string.

    :param version: Version string that needs to be parsed
    :return: a stripped version string of the format MAJOR[.MINOR[.PATCH]]
    """
    result = re.match(r'\d+(\.\d+){0,2}', version)
    if result:
        return result.group(0)
    else:
        raise FatalError('''Unable to parse version '{}'.'''.format(version))
