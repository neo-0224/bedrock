# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import jinja2
from django_jinja import library

from lib.l10n_utils.fluent import translate


@library.global_function
@jinja2.contextfunction
def fluent(ctx, string_id, **args):
    return translate(string_id, ctx['ftl_files'], args)
