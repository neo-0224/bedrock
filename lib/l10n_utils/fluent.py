import json
from functools import wraps
from hashlib import md5

from django.conf import settings
from django.core.cache import caches
from django.utils.encoding import force_bytes
from django.utils.functional import lazy, cached_property

from fluent.runtime import FluentLocalization, FluentResourceLoader
from fluent.syntax.ast import GroupComment, Message


__all__ = [
    'fluent_l10n',
    'has_any_messages',
    'has_all_messages',
    'translate',
    'ftl',
    'ftl_lazy',
]
cache = caches['l10n']


class FluentL10n(FluentLocalization):
    def _localized_bundles(self):
        for bundle in self._bundles():
            if bundle.locales[0] == self.locales[0]:
                yield bundle

    @cached_property
    def _messages(self):
        messages = {}
        for bundle in self._bundles():
            messages.update(bundle._messages)

        return messages

    @cached_property
    def _localized_messages(self):
        messages = {}
        for bundle in self._localized_bundles():
            messages.update(bundle._messages)

        return messages

    @cached_property
    def required_message_ids(self):
        """
        Look in the "en" file for message IDs grouped by a comment that starts with "Required"

        :return: list of message IDs
        """
        messages = set()
        for resources in self.resource_loader.resources('en', self.resource_ids):
            for resource in resources:
                in_required = False
                for item in resource.body:
                    if isinstance(item, GroupComment):
                        in_required = item.content.lower().startswith('required')
                        continue

                    if isinstance(item, Message) and in_required:
                        messages.add(item.id.name)

        return list(messages)

    @cached_property
    def has_required_messages(self):
        return all(self.has_message(m) for m in self.required_message_ids)

    @cached_property
    def active_locales(self):
        if settings.DEV:
            return settings.DEV_LANGUAGES if settings.DEV else settings.PROD_LANGUAGES

        # first resource is the one to check for activation
        return get_active_locales(self.resource_ids[0])

    @cached_property
    def percent_translated(self):
        return (float(len(self._localized_messages)) / float(len(self._messages))) * 100

    def has_message(self, message_id):
        # assume English locales have the message
        if self.locales[0].startswith('en-'):
            return True

        return message_id in self._localized_messages


def _cache_key(*args, **kwargs):
    key = f'fluent:{args}:{kwargs}'
    return md5(force_bytes(key)).hexdigest()


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
def get_active_locales(ftl_file):
    metadata_file = settings.FLUENT_REPO_PATH.joinpath('metadata', ftl_file).with_suffix('.json')
    locales = [settings.LANGUAGE_CODE]
    if metadata_file.exists():
        with metadata_file.open() as mf:
            metadata = json.load(mf)
            locales.extend(metadata['active_locales'])

    return locales


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


# alias for use in views
ftl = translate
# for use in python outside of a view
ftl_lazy = lazy(translate, str)
