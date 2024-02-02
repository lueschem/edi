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

from edi.commands.project import Project


class Clean(Project):
    @classmethod
    def advertise(cls, subparsers):
        help_text = "EXPERIMENTAL: clean all intermediate project artifacts"
        description_text = "EXPERIMENTAL: Clean all intermediate project artifacts."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self.run(cli_args.config_file)

    def run(self, config_file):
        self.clean(config_file)

    def clean(self, config_file):
        self._clean_siblings_and_sub_commands(config_file)
