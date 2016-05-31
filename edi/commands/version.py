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

from setuptools_scm import get_version
from edi.lib.edicommand import EdiCommand
from os.path import abspath, join, dirname, isdir
import pkg_resources


class Version(EdiCommand):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "print the program version"
        description_text = "Print the program version."
        subparsers.add_parser(cls._get_short_command_name(),
                              help=help_text,
                              description=description_text)

    def run_cli(self, _):
        version = self.run()
        print(version)

    def run(self):
        project_root = abspath(join(dirname(__file__), "../.."))
        git_dir = join(project_root, ".git")
        if isdir(git_dir):
            return get_version(root=project_root)
        else:
            return pkg_resources.get_distribution('edi').version
