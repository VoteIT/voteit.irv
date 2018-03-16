# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
from math import ceil

from stvpoll import ElectionRound, IncompleteResult, Candidate

from stvpoll import STVPollBase


def irv_quota(poll):
    # type: (STVPollBase) -> int
    return int(ceil(Decimal(poll.ballot_count + poll.result.empty_ballot_count) / 2))


class IRV(STVPollBase):
    def __init__(self, seats, candidates, quota=irv_quota, random_in_tiebreaks=True):
        super(IRV, self).__init__(1, candidates, quota, random_in_tiebreaks)

    def calculate_round(self):
        # type: () -> None

        # First, check if there is a winner
        winners = filter(lambda c: c.votes >= self.quota, self.standing_candidates)
        if len(winners) > 1:  # Extreme case of two candidates with 50 %
            winner, method = self.resolve_tie(winners)
            self.select(winner, method)
            self.transfer_votes(winner)

        elif len(winners) == 1:
            winner = winners[0]
            self.select(winner, ElectionRound.SELECTION_METHOD_DIRECT)
            self.transfer_votes(winner)

        else:
            if len(self.standing_candidates) == 1:
                raise IncompleteResult('No more candidates can get majority.')

            loser, method = self.get_candidate(most_votes=False)
            self.select(loser, method, Candidate.EXCLUDED)
            self.transfer_votes(loser)


class RepeatedIRV(STVPollBase):
    def __init__(self, seats, candidates, quota=irv_quota, random_in_tiebreaks=True):
        super(RepeatedIRV, self).__init__(seats, candidates, quota, random_in_tiebreaks)

    def calculate_round(self):
        # type: () -> None
        singular_irv = IRV(1, [c.obj for c in self.standing_candidates],
                           quota=self._quota_function,
                           random_in_tiebreaks=self.random_in_tiebreaks)
        for ballot in self.ballots:
            singular_irv.add_ballot([c.obj for c in ballot.preferences if c in self.standing_candidates], ballot.count)
        singular_irv.calculate()

        if not singular_irv.result.complete:
            raise IncompleteResult('No more candidates can get majority.')

        winner = [c for c in self.candidates if c == singular_irv.result.elected[0]][0]
        self.select(winner, ElectionRound.SELECTION_METHOD_DIRECT)
