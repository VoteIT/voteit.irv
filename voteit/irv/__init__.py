from pyramid.i18n import TranslationStringFactory
from pyramid_deform import configure_zpt_renderer

_ = TranslationStringFactory('voteit.irv')


def includeme(config):
    config.include('.models')
    config.include('.fanstatic_lib')
    config.add_translation_dirs('voteit.irv:locale/')
    configure_zpt_renderer(['voteit.irv:templates/deform'])
