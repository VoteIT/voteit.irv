from __future__ import unicode_literals

from .poll import IRV
from .poll import RepeatedIRV
from voteit.stv.models import ScottishSTVPoll

from voteit.irv import _
from voteit.irv.schemas import IRVPollSchema
from voteit.irv.schemas import SettingsSchema


class IRVPoll(ScottishSTVPoll):
    name = 'irv'
    title = _("Instant-runoff voting")
    description = _("moderator_description_irv",
                    default="Ranked poll with single winner. "
                            "Voters rank proposals by order of preference. "
                            "First proposal with majority wins.")
    voter_description = _("voter_description_irv",
                          default="Rank proposals by order of preference. "
                                  "Your vote will be transferred according to your list as proposals are excluded. "
                                  "First proposal with majority wins.")
    method = IRV
    template_name = 'voteit.irv:templates/result_irv.pt'

    def get_vote_schema(self):
        return IRVPollSchema()

    def get_settings_schema(self):
        pass


class RepeatedIRVPoll(IRVPoll):
    name = 'repeated_irv'
    title = _("Repeated IRV")
    description = _("moderator_description_repeated_irv",
                    default="Non-proportional ranked poll with multiple winners. "
                            "WARNING: Result is easily manipulated by a group of voters.")
    voter_description = _("voter_description_repeated_irv",
                          default="Rank proposals by order of preference. "
                                  "Your vote will be transferred according to your list as proposals are excluded. "
                                  "Winners is decided by majority, and repeats until all winners are selected.")
    method = RepeatedIRV
    template_name = 'voteit.irv:templates/result_repeated_irv.pt'

    def get_settings_schema(self):
        return SettingsSchema()


def includeme(config):
    config.registry.registerAdapter(RepeatedIRVPoll, name=RepeatedIRVPoll.name)
    config.registry.registerAdapter(IRVPoll, name=IRVPoll.name)
