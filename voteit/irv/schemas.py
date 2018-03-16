from __future__ import unicode_literals

import colander
import deform
from pyramid.traversal import find_interface
from six import string_types

from voteit.stv import _

from voteit.core.models.interfaces import IPoll


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


class ProposalOrderingWidget(deform.widget.Widget):
    template = 'sorting'
    readonly_template = 'sorting'  # FIXME
    proposals = {}

    def serialize(self, field, cstruct, **kw):
        if cstruct in (colander.null, None):
            cstruct = ()
        readonly = kw.get('readonly', self.readonly)
        proposals = kw.get('proposals', self.proposals)
        kw['prop_dict'] = prop_dict = self.as_dict(proposals)
        kw['pool'] = set(prop_dict.keys()) - set(cstruct)
        template = readonly and self.readonly_template or self.template
        tmpl_values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **tmpl_values)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        if isinstance(pstruct, string_types):
            return (pstruct,)
        return tuple(pstruct)

    def as_dict(self, proposals):
        return dict([(x.uid, x) for x in proposals])


@colander.deferred
def proposals_ordering_widget(node, kw):
    context = kw['context']
    return ProposalOrderingWidget(proposals = context.get_proposal_objects())


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
        widget=proposals_ordering_widget,
        validator=n_must_be_picked_validator,
    )
