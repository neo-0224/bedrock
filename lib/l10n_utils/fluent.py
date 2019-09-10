from hashlib import md5

from django.conf import settings
from django.core.cache import caches
from django.utils.encoding import force_bytes

from fluent.runtime import FluentLocalization, RootedFileResourceLoader

from lib.l10n_utils import translation


cache = caches['l10n']


def _fluent_cache_key(*args):
    hash = md5(b'fluent-bundle')
    for arg in args:
        if arg is None:
            hash.update(b'None')
        elif isinstance(arg, str):
            hash.update(force_bytes(arg))
        elif isinstance(arg, dict):
            hash.update(b':'.join([force_bytes(f'{k}={v}') for k, v in arg.items()]))
        else:
            hash.update(b':'.join([force_bytes(a) for a in arg]))

    return hash.hexdigest()


def fluent_bundle(locales, files):
    key = _fluent_cache_key(locales, files)
    bundle = cache.get(key)
    if bundle is None:
        if isinstance(locales, str):
            locales = [locales]

        # file IDs may not have file extension
        files = [f'{f}.ftl' for f in files if not f.endswith('.ftl')]
        # temporary until MultiRootLoader lands
        path = f'{settings.FLUENT_PATHS[1]}/{{locale}}/'
        loader = RootedFileResourceLoader(path)
        bundle = FluentLocalization(locales, files, loader)
        cache.set(key, bundle)

    return bundle


def has_message(message_id, bundle):
    if not bundle._bundle_cache:
        # need to warm the cache in the bundle
        bundle.format_value('warm')

    return bundle._bundle_cache[0].has_message(message_id)


def has_all_messages(message_ids, files):
    locale = translation.get_language(True)
    bundle = fluent_bundle(locale, files)
    return all([has_message(mid, bundle) for mid in message_ids])


def translate(message_id, files, fallback=None, **args):
    locale = translation.get_language(True)
    key = _fluent_cache_key(locale, message_id, files, fallback, args)
    value = cache.get(key)
    if value is None:
        bundle = fluent_bundle([locale, 'en'], files)
        # check the `locale` bundle for the message if we have a fallback defined
        if fallback and not has_message(message_id, bundle):
            value = bundle.format_value(fallback, args)
        else:
            value = bundle.format_value(message_id, args)

        cache.set(key, value)

    return value
