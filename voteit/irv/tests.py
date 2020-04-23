from __future__ import unicode_literals

import unittest

from pyramid import testing
from stvpoll import STVPollBase
from typing import Type

from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.meeting import Meeting
from voteit.core.models.poll import Poll
from voteit.core.models.proposal import Proposal
from voteit.core.security import unrestricted_wf_transition_to
from voteit.core.testing_helpers import bootstrap_and_fixture
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject


class IRVTests(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from .models import RepeatedIRVPoll
        return RepeatedIRVPoll

    def test_verify_class(self):
        self.failUnless(verifyClass(IPollPlugin, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IPollPlugin, self._cut(testing.DummyModel())))

    def test_format_ballots(self):
        poll = _setup_poll_fixture(self.config)
        # We need a proper poll plugin for this test
        poll.poll_plugin = 'repeated_irv'
        _add_votes(poll)
        poll.ballots = poll.calculate_ballots()
        # poll.close_poll()
        plugin = poll.get_poll_plugin()
        # plugin.handle_close()
        self.assertEqual(plugin.format_ballots(),
                         [{'count': 3, 'ballot': ["p1uid", "p2uid", "p3uid"]}])

    def test_render_raw_data(self):
        poll = _setup_poll_fixture(self.config)
        poll.poll_plugin = 'repeated_irv'
        _add_votes(poll)
        poll.close_poll()
        plugin = poll.get_poll_plugin()
        # Same as poll.ballots, but as a string
        self.assertEqual(plugin.render_raw_data().body, "(({u'proposals': (u'p1uid', u'p2uid', u'p3uid')}, 3),)")

    def test_handle_close(self):
        poll = _setup_poll_fixture(self.config)
        poll.poll_plugin = 'repeated_irv'
        _add_votes(poll)
        poll.close_poll()
        self.assertEqual(set(poll.poll_result['candidates']), {'p1uid', 'p2uid', 'p3uid'})
        self.assertEqual(set(poll.poll_result['winners']), {'p1uid'})
        self.assertEqual(poll.poll_result['quota'], 2)
        self.assertEqual(poll.poll_result['complete'], True)

    def test_close_no_votes(self):
        poll = _setup_poll_fixture(self.config)
        poll.poll_plugin = 'irv'
        poll.close_poll()
        self.assertEqual(set(poll.poll_result['candidates']), {'p1uid', 'p2uid', 'p3uid'})
        self.assertEqual(len(poll.poll_result['winners']), 1)
        self.assertEqual(poll.poll_result['complete'], True)

    def test_handle_close_2_winners(self):
        poll = _setup_poll_fixture(self.config)
        poll.poll_plugin = 'repeated_irv'
        poll.poll_settings['winners'] = 2
        _add_votes(poll)
        poll.close_poll()
        self.assertEqual(set(poll.poll_result['winners']), {'p1uid', 'p2uid'})
        self.assertEqual(poll.poll_result['complete'], True)

    def test_handle_close_2_winners_opa_example(self):
        poll = _setup_poll_fixture(self.config)
        poll.poll_plugin = 'repeated_irv'
        poll.poll_settings['winners'] = 3
        _opa_fixture(poll)
        poll.close_poll()
        self.assertEqual(set(poll.poll_result['winners']), {'Alice', 'Bob', 'Chris'})
        self.assertEqual(poll.poll_result['complete'], True)


def _setup_poll_fixture(config):
    config.testing_securitypolicy('admin', permissive = True)
    # config.include('pyramid_chameleon')
    # Register plugin
    config.include('voteit.irv')
    config.include('arche.testing')
    config.include('arche.testing.workflow')
    config.include('arche.testing.catalog')
    config.include('voteit.core.models.catalog')
    root = bootstrap_and_fixture(config)
    root['m'] = Meeting()
    unrestricted_wf_transition_to(root['m'], 'ongoing')
    root['m']['ai'] = ai = AgendaItem()
    unrestricted_wf_transition_to(ai, 'upcoming')
    unrestricted_wf_transition_to(ai, 'ongoing')
    # Setup poll
    ai['poll'] = Poll()
    poll = ai['poll']
    # Add proposals
    p1 = Proposal(creators = ['dummy'], text = 'first proposal')
    p1.uid = 'p1uid' #To make it simpler to test against
    ai['p1'] = p1
    p2 = Proposal(creators = ['dummy'], text = 'second proposal')
    p2.uid = 'p2uid'
    ai['p2'] = p2
    p3 = Proposal(creators = ['dummy'], text = 'third proposal')
    p3.uid = 'p3uid'
    ai['p3'] = p3
    # Select proposals for this poll
    poll.proposal_uids = (p1.uid, p2.uid, p3.uid)
    # Set poll as ongoing
    unrestricted_wf_transition_to(poll, 'upcoming')
    return poll


def _add_votes(poll):
    plugin = poll.get_poll_plugin()
    # Add 3 votes
    vote_data = ("p1uid", "p2uid", "p3uid",)
    for name in ('one', 'two', 'three'):
        vote = plugin.get_vote_class()(creators = [name])
        vote.set_vote_data({'proposals': vote_data}, notify=False)
        poll[name] = vote


def _opa_fixture(poll):
    count = {'a': 28, 'b': 26, 'c': 3, 'd': 2, 'e': 1}
    ballot = {
        'a': ['Alice', 'Bob', 'Chris'],
        'b': ['Bob', 'Alice', 'Chris'],
        'c': ['Chris'],
        'd': ['Don'],
        'e': ['Eric']
    }
    candidates = ['Alice', 'Bob', 'Chris', 'Don', 'Eric']
    ai = poll.__parent__
    for cand in candidates:
        prop = Proposal(creators=['dummy'], text=cand, uid=cand)
        ai[cand] = prop
    poll.proposal_uids = tuple(candidates)

    # Setup poll
    plugin = poll.get_poll_plugin()
    Vote = plugin.get_vote_class()
    for btype in ballot:
        for i in range(count[btype]):
            name = "%s-%s" % (btype, i)
            vote = Vote()
            vote.set_vote_data({'proposals': tuple(ballot[btype])})
            poll[name] = vote


def _opa_example_fixture(factory):
    """
    28 voters ranked Alice first, Bob second, and Chris third
    26 voters ranked Bob first, Alice second, and Chris third
    3 voters ranked Chris first
    2 voters ranked Don first
    1 voter ranked Eric first
    """
    obj = factory(seats=3, candidates=['Alice', 'Bob', 'Chris', 'Don', 'Eric'])
    obj.add_ballot(['Alice', 'Bob', 'Chris'], 28)
    obj.add_ballot(['Bob', 'Alice', 'Chris'], 26)
    obj.add_ballot(['Chris'], 3)
    obj.add_ballot(['Don'], 2)
    obj.add_ballot(['Eric'], 1)
    return obj


def _wikipedia_example_fixture(factory):
    """
    Example from https://en.wikipedia.org/wiki/Single_transferable_vote
    """
    example_ballots = (
        (('orange',), 4),
        (('pear', 'orange',), 2),
        (('chocolate', 'strawberry',), 8),
        (('chocolate', 'bonbon',), 4),
        (('strawberry',), 1),
        (('bonbon',), 1),
    )
    obj = factory(seats=3, candidates=('orange', 'chocolate', 'pear', 'strawberry', 'bonbon'))
    for b in example_ballots:
        obj.add_ballot(*b)
    return obj


def _incomplete_result_fixture(factory):
    # type: (Type[STVPollBase]) -> STVPollBase
    example_ballots = (
        (('Batman',), 1),
        (('Gorm',), 2),
    )
    obj = factory(seats=3, candidates=('Andrea', 'Batman', 'Robin', 'Gorm'), random_in_tiebreaks=False)
    for b in example_ballots:
        obj.add_ballot(*b)
    return obj


class RepeatedIRVTests(unittest.TestCase):
    opa_results = {'Alice', 'Bob', 'Chris'}
    wiki_results = {'chocolate'}
    wiki_cpo_results = {'Carter', 'Scott', 'Andrea'}

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        # type: () -> Type[RepeatedIRV]
        from .poll import RepeatedIRV
        return RepeatedIRV

    def test_opa_example(self):
        obj = _opa_example_fixture(self._cut)
        result = obj.calculate()
        self.assertEqual(result.elected_as_set(), self.opa_results)
        self.assertEqual(result.as_dict()['randomized'], False)
        self.assertEqual(result.as_dict()['complete'], True)

    def test_wikipedia_example(self):  # Incomplete!
        obj = _wikipedia_example_fixture(self._cut)
        result = obj.calculate()
        self.assertEqual(result.elected_as_set(), self.wiki_results)
        self.assertEqual(len(result.elected_as_set()), 1)
        self.assertEqual(result.as_dict()['randomized'], False)
        self.assertEqual(result.as_dict()['complete'], False)

    def test_incomplete_result(self):
        obj = _incomplete_result_fixture(self._cut)
        result = obj.calculate()
        self.assertEqual(result.as_dict()['randomized'], False)
        self.assertEqual(result.as_dict()['complete'], False)
