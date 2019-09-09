from django.conf import settings
from django.core.cache import caches

from fluent.runtime import FluentLocalization, RootedFileResourceLoader

from lib.l10n_utils import translation


cache = caches['l10n']


def _fluent_cache_key(*args):
    key = ['fluent-bundle']
    for arg in args:
        if isinstance(arg, str):
            key.append(arg)
        elif isinstance(arg, dict):
            key.extend([f'k-v' for k, v in arg.items()])
        else:
            key.extend(arg)

    return '-'.join(key)


def fluent_bundle(locales, files):
    key = _fluent_cache_key(locales, files)
    bundle = cache.get(key)
    if bundle is None:
        files = [f'{f}.ftl' for f in files]
        # temporary until MultiRootLoader lands
        path = f'{settings.FLUENT_PATHS[1]}/{{locale}}/'
        loader = RootedFileResourceLoader(path)
        bundle = FluentLocalization(locales, files, loader)
        cache.set(key, bundle)

    return bundle


def translate(string_id, files, args):
    lang = translation.get_language(True)
    key = _fluent_cache_key(lang, string_id, files, args)
    value = cache.get(key)
    if value is None:
        bundle = fluent_bundle([lang, 'en'], files)
        value = bundle.format_value(string_id, args)
        cache.set(key, value)

    return value
