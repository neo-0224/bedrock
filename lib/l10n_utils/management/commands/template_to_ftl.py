# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
from django.utils.functional import cached_property
from hashlib import md5
from io import StringIO
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from lib.l10n_utils.extract import tweak_message
from lib.l10n_utils.utils import get_ftl_file_data


GETTEXT_RE = re.compile(r'\b_\([\'"]([^)]+)[\'"]\)')
FORMAT_RE = re.compile(r'\)\s*\|\s*format\(')


class Command(BaseCommand):
    help = 'Convert a template to use Fluent for l10n'
    _filename = None
    _template = None

    def add_arguments(self, parser):
        parser.add_argument('ftl_file')
        parser.add_argument('template')
        parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', default=False,
                            help='If no error occurs, swallow all output.'),
        parser.add_argument('-f', '--force', action='store_true', dest='force', default=False,
                            help='Overwrite the FTL template if it exists.'),

    @property
    def filename(self):
        if self._filename is None:
            return ''

        return self._filename

    @filename.setter
    def filename(self, value):
        if not value.endswith('.ftl'):
            self._filename = f'{value}.ftl'
        else:
            self._filename = value

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, value):
        self._template = Path(value)

    @property
    def ftl_template(self):
        ftl_template = f'{self.template.stem}_ftl.html'
        return self.template.with_name(ftl_template)

    @cached_property
    def ftl_file_data(self):
        return get_ftl_file_data(self.filename)

    def template_replace(self, match):
        ftl_data = self.ftl_file_data
        str_id = tweak_message(match.group(1))
        str_hash = md5(str_id.encode()).hexdigest()
        ftl_id = ftl_data.get(str_hash)
        if ftl_id:
            return f"ftl('{ftl_id}')"

        return match.group(0)

    def ftl_template_lines(self):
        new_lines = []
        with self.template.open('r') as tfp:
            for line in tfp:
                fixed_line = GETTEXT_RE.sub(self.template_replace, line)
                fixed_line = FORMAT_RE.sub(', ', fixed_line)
                new_lines.append(fixed_line)
                self.stdout.write('.', ending='')
                self.stdout.flush()

        return new_lines

    def write_ftl_template(self):
        with self.ftl_template.open('w') as ftlt:
            ftlt.writelines(self.ftl_template_lines())

    def handle(self, *args, **options):
        self.filename = options['ftl_file']
        self.template = options['template']
        if options['quiet']:
            self.stdout._out = StringIO()

        if self.ftl_template.exists() and not options['force']:
            raise CommandError('Output file exists. Use --force to overwrite.')

        self.write_ftl_template()
        self.stdout.write('\nDone')
