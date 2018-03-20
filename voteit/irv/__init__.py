from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('voteit.irv')


def includeme(config):
    config.include('.models')
    config.add_translation_dirs('voteit.irv:locale/')
