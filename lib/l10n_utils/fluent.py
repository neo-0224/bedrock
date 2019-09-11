from functools import wraps
from hashlib import sha256

from django.conf import settings
from django.core.cache import caches
from django.utils.encoding import force_bytes

from fluent.runtime import FluentLocalization, FluentResourceLoader


cache = caches['l10n']


class FluentL10n(FluentLocalization):
    _localized_messages = None

    def _localized_bundles(self):
        for bundle in self._bundles():
            if bundle.locales[0] == self.locales[0]:
                yield bundle

    @property
    def localized_messages(self):
        if self._localized_messages is None:
            self._localized_messages = {}
            for bundle in self._localized_bundles():
                self._localized_messages.update(bundle._messages)

        return self._localized_messages

    def has_message(self, message_id):
        # assume English locales have the message
        if self.locales[0].startswith('en-') or settings.DEV:
            return True

        return message_id in self.localized_messages


def _cache_key(*args, **kwargs):
    key = f'fluent:{args}:{kwargs}'
    return sha256(force_bytes(key)).hexdigest()


def memoize(f):
    """Decorator to cache the results of expensive functions"""
    @wraps(f)
    def inner(*args, **kwargs):
        key = _cache_key(f.__name__, *args, **kwargs)
        value = cache.get(key)
        if value is None:
            value = f(*args, **kwargs)
            cache.set(key, value)

        return value

    return inner


@memoize
def fluent_l10n(locales, files):
    if isinstance(locales, str):
        locales = [locales]

    # file IDs may not have file extension
    files = [f'{f}.ftl' for f in files if not f.endswith('.ftl')]
    paths = [f'{path}/{{locale}}/' for path in settings.FLUENT_PATHS]
    loader = FluentResourceLoader(paths)
    return FluentL10n(locales, files, loader)


@memoize
def _has_messages(l10n, message_ids):
    return [l10n.has_message(mid) for mid in message_ids]


def has_all_messages(l10n, message_ids):
    return all(_has_messages(l10n, message_ids))


def has_any_messages(l10n, message_ids):
    return any(_has_messages(l10n, message_ids))


@memoize
def translate(l10n, message_id, fallback=None, **kwargs):
    # check the `locale` bundle for the message if we have a fallback defined
    if fallback and not l10n.has_message(message_id):
        message_id = fallback

    return l10n.format_value(message_id, kwargs)
