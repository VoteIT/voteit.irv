from __future__ import unicode_literals

import colander
import deform
from pyramid.traversal import find_interface
from voteit.stv.schemas import proposals_ordering_widget
from voteit.core.models.interfaces import IPoll

from voteit.irv import _


class SettingsSchema(colander.Schema):
    """ Settings for a Repeated IRV poll
    """
    winners = colander.SchemaNode(
        colander.Int(),
        title=_("Winners"),
        description=_("repeated_irv_config_winners_description",
                      default="Numbers of possible winners in the poll."),
        default=1,
    )
    min_ranked = colander.SchemaNode(
        colander.Int(),
        title=_("Minimum ranked candidates"),
        description=_("repeated_irv_config_min_ranked_description",
                      default="Minimum number of candidates to rank."),
        default=1,
    )


@colander.deferred
def n_must_be_picked_validator(node, kw):
    context = kw['context']
    poll = find_interface(context, IPoll)
    return ContainsAtLeast(poll.poll_settings.get('min_ranked'))


class ContainsAtLeast(object):
    """ Input must contain exactly all of the values passed as initial choices.
        The order is irrelevant though.
    """

    def __init__(self, min):
        self.min = min

    def __call__(self, node, value):
        if len(value) < self.min:
            msg = _("You must vote for at least ${num} proposals.",
                    mapping={'num': self.min})
            raise colander.Invalid(node, msg)


# The schema will be populated in the irv poll plugin
class IRVPollSchema(colander.Schema):
    widget = deform.widget.FormWidget(
        template='form_modal',
        readonly_template='readonly/form_modal'
    )
    proposals = colander.SchemaNode(
        colander.List(),
        title = _("Proposals"),
        widget=proposals_ordering_widget,
        validator=n_must_be_picked_validator,
    )
