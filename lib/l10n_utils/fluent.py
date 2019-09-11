from functools import wraps
from hashlib import sha256

from django.conf import settings
from django.core.cache import caches
from django.utils.encoding import force_bytes

from fluent.runtime import FluentLocalization, RootedFileResourceLoader

from lib.l10n_utils import translation


cache = caches['l10n']


def _cache_key(*args, **kwargs):
    return sha256(force_bytes(f'fluent:{args}:{kwargs}')).hexdigest()


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
def fluent_bundle(locales, files):
    if isinstance(locales, str):
        locales = [locales]

    # file IDs may not have file extension
    files = [f'{f}.ftl' for f in files if not f.endswith('.ftl')]
    # temporary until MultiRootLoader lands
    path = f'{settings.FLUENT_PATHS[1]}/{{locale}}/'
    loader = RootedFileResourceLoader(path)
    return FluentLocalization(locales, files, loader)


def has_message(message_id, bundle):
    # assume English locales have the message
    if bundle.locales[0].startswith('en-'):
        return True

    if not bundle._bundle_cache:
        # need to warm the cache in the bundle
        bundle.format_value('warm')

    if not bundle._bundle_cache:
        # still no bundles in the cache, no ftl file
        return False

    return bundle._bundle_cache[0].has_message(message_id)


@memoize
def _has_messages(locale, message_ids, files):
    bundle = fluent_bundle(locale, files)
    return all([has_message(mid, bundle) for mid in message_ids])


def has_all_messages(message_ids, files):
    locale = translation.get_language(True)
    return _has_messages(locale, message_ids, files)


@memoize
def _get_translation(locale, message_id, files, fallback, **kwargs):
    bundle = fluent_bundle([locale, 'en'], files)
    # check the `locale` bundle for the message if we have a fallback defined
    if fallback and not has_message(message_id, bundle):
        message_id = fallback

    return bundle.format_value(message_id, kwargs)


def translate(message_id, files, fallback=None, **kwargs):
    locale = translation.get_language(True)
    return _get_translation(locale, message_id, files, fallback, **kwargs)
