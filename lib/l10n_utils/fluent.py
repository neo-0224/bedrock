from django.conf import settings

from fluent.runtime import FluentBundle, FluentResource

from lib.l10n_utils import translation


def fluent_path(filename, lang):
    return settings.FLUENT_LOCAL_PATH.joinpath(lang, filename).with_suffix('.ftl')


def translate(string_id, files):
    lang = translation.get_language(True)
    bundles = {
        lang: FluentBundle([lang]),
        'en': FluentBundle(['en']),
    }
    for file in files:
        for bundle_lang in [lang, 'en']:
            filepath = fluent_path(file, bundle_lang)
            try:
                with filepath.open() as fh:
                    resource = FluentResource(fh.read())
                    bundles[bundle_lang].add_resource(resource)
            except FileNotFoundError:
                pass

    try:
        lang_str, errors = bundles[lang].format_pattern(bundles[lang].get_message(string_id).value)
    except KeyError:
        lang_str, errors = bundles['en'].format_pattern(bundles['en'].get_message(string_id).value)

    return lang_str
