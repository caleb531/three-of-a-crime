#!/usr/bin/env python3

import io
import json
import glob
import nose.tools as nose
import radon.complexity as radon
import toac.player as player
from mock import Mock, NonCallableMock, patch
from decorators import redirect_stdout


BASE_SUSPECTS = {'pto', 'nnn', 'jco', 'lel', 'lsl', 'kca', 'hbu'}
MAX_COMPLEXITY = 5

def test_transform_data():
    '''should transform input data by converting lists to sets as necessary'''
    data = {
        'base_suspects': [], 'match_length': 3,
        'cards': [
            {'suspects': [], 'match_count': 2},
            {'suspects': [], 'match_count': 1},
            {'suspects': [], 'match_count': 0}
        ],
        'previous_guesses': [
            ['kca', 'nnn', 'hbu'],
            ['lsl', 'pto', 'nnn']
        ]
    }
    player.transform_data(data)
    nose.assert_is_instance(data['base_suspects'], frozenset)
    nose.assert_is_instance(data['cards'], list)
    for card in data['cards']:
        yield nose.assert_is_instance, card['suspects'], frozenset
    for guess in data['previous_guesses']:
        yield nose.assert_is_instance, guess, frozenset
    nose.assert_is_instance(data['previous_guesses'], frozenset)


class TestRemoveImpossibleSuspects(object):
    '''remove_impossible_suspects should behave as expected in all cases'''

    def setup(self):
        self.base_suspects = set(BASE_SUSPECTS)

    def test_same_reference(self):
        '''should modify base suspect set'''
        cards = []
        old_base_suspects = self.base_suspects
        player.remove_impossible_suspects(cards, self.base_suspects)
        nose.assert_set_equal(self.base_suspects, old_base_suspects)

    def test_remove_impossible_suspects(self):
        '''should remove impossible suspects from base suspect set'''
        cards = [
            {'suspects': {'pto', 'lsl', 'jco'}, 'match_count': 1},
            {'suspects': {'nnn', 'pto', 'hbu'}, 'match_count': 2},
            {'suspects': {'kca', 'pto', 'lel'}, 'match_count': 2},
            {'suspects': {'kca', 'nnn', 'lsl'}, 'match_count': 0}
        ]
        player.remove_impossible_suspects(cards, self.base_suspects)
        nose.assert_set_equal(self.base_suspects, {'pto', 'jco', 'lel', 'hbu'})

    def test_fail_silently(self):
        '''should not raise exception if suspect has already been removed'''
        cards = [
            {'suspects': ['lel', 'lsl', 'kca'], 'match_count': 0},
            {'suspects': ['jco', 'lsl', 'hbu'], 'match_count': 1},
            {'suspects': ['kca', 'nnn', 'pto'], 'match_count': 2},
            {'suspects': ['lel', 'hbu', 'kca'], 'match_count': 0}
        ]
        player.remove_impossible_suspects(cards, self.base_suspects)
        nose.assert_set_equal(self.base_suspects, {'pto', 'jco', 'nnn'})


class TestRemoveGuessesFromMatches(object):
    '''remove_guesses_from_matches should behave as expected in all cases'''

    def setup(self):
        self.guesses = {
            frozenset({'kca', 'nnn', 'hbu'}),
            frozenset({'lsl', 'pto', 'nnn'})
        }
        self.matches = set(self.guesses)

    def test_same_reference(self):
        '''should modify set of matches'''
        old_matches = self.matches
        player.remove_guesses_from_matches(self.matches, self.guesses)
        nose.assert_set_equal(self.matches, old_matches)

    def test_matches_one_guess(self):
        '''should remove all guesses from set of matches'''
        first_guess, second_guess = self.guesses
        player.remove_guesses_from_matches(
            self.matches, {first_guess})
        nose.assert_set_equal(self.matches, {second_guess})


def test_get_matches():
    '''should correctly find all possible matches given some data'''
    data = {
      'base_suspects': frozenset(BASE_SUSPECTS),
      'match_length': 3,
      'cards': [
        {'suspects': {'pto', 'lsl', 'jco'}, 'match_count': 1},
        {'suspects': {'nnn', 'pto', 'hbu'}, 'match_count': 2},
        {'suspects': {'kca', 'pto', 'lel'}, 'match_count': 2},
        {'suspects': {'kca', 'nnn', 'lsl'}, 'match_count': 0}
      ],
      'previous_guesses': []
    }
    matches = player.get_matches(**data)
    nose.assert_set_equal(matches, {frozenset({'lel', 'pto', 'hbu'})})


@patch('sys.stdin', NonCallableMock(read=Mock(return_value='{"cards": []}')))
@patch('toac.player.transform_data', return_value={'cards': set()})
@patch(
    'toac.player.get_matches', return_value={frozenset({'hbu', 'kca', 'pto'})})
@redirect_stdout
def test_main(out, get_matches, transform_data):
    '''should accept input and produce correct output when run from CLI'''
    player.main()
    transform_data.assert_called_once_with({'cards': []})
    output = out.getvalue()
    nose.assert_equal(output, output.strip())
    match = set(json.loads(output))
    nose.assert_set_equal(match, {'hbu', 'kca', 'pto'})
