#!/usr/bin/env python3

import json
import unittest
import toac.player as player
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, NonCallableMock, patch

case = unittest.TestCase()


BASE_SUSPECTS = {"pto", "nnn", "jco", "lel", "lsl", "kca", "hbu"}
MAX_COMPLEXITY = 5


def test_transform_data():
    """should transform input data by converting lists to sets as necessary"""
    data = {
        "base_suspects": [],
        "match_length": 3,
        "cards": [
            {"suspects": [], "match_count": 2},
            {"suspects": [], "match_count": 1},
            {"suspects": [], "match_count": 0},
        ],
        "previous_guesses": [["kca", "nnn", "hbu"], ["lsl", "pto", "nnn"]],
    }
    player.transform_data(data)
    case.assertIsInstance(data["base_suspects"], frozenset)
    case.assertIsInstance(data["cards"], list)
    for card in data["cards"]:
        yield case.assertIsInstance, card["suspects"], frozenset
    for guess in data["previous_guesses"]:
        yield case.assertIsInstance, guess, frozenset
    case.assertIsInstance(data["previous_guesses"], frozenset)


class TestRemoveImpossibleSuspects(object):
    """remove_impossible_suspects should behave as expected in all cases"""

    def setUp(self):
        self.base_suspects = set(BASE_SUSPECTS)

    def test_same_reference(self):
        """should modify base suspect set"""
        cards = []
        old_base_suspects = self.base_suspects
        player.remove_impossible_suspects(cards, self.base_suspects)
        case.assertSetEqual(self.base_suspects, old_base_suspects)

    def test_remove_impossible_suspects(self):
        """should remove impossible suspects from base suspect set"""
        cards = [
            {"suspects": {"pto", "lsl", "jco"}, "match_count": 1},
            {"suspects": {"nnn", "pto", "hbu"}, "match_count": 2},
            {"suspects": {"kca", "pto", "lel"}, "match_count": 2},
            {"suspects": {"kca", "nnn", "lsl"}, "match_count": 0},
        ]
        player.remove_impossible_suspects(cards, self.base_suspects)
        case.assertSetEqual(self.base_suspects, {"pto", "jco", "lel", "hbu"})

    def test_fail_silently(self):
        """should not raise exception if suspect has already been removed"""
        cards = [
            {"suspects": ["lel", "lsl", "kca"], "match_count": 0},
            {"suspects": ["jco", "lsl", "hbu"], "match_count": 1},
            {"suspects": ["kca", "nnn", "pto"], "match_count": 2},
            {"suspects": ["lel", "hbu", "kca"], "match_count": 0},
        ]
        player.remove_impossible_suspects(cards, self.base_suspects)
        case.assertSetEqual(self.base_suspects, {"pto", "jco", "nnn"})


class TestRemoveGuessesFromMatches(object):
    """remove_guesses_from_matches should behave as expected in all cases"""

    def setUp(self):
        self.guesses = {
            frozenset({"kca", "nnn", "hbu"}),
            frozenset({"lsl", "pto", "nnn"}),
        }
        self.matches = set(self.guesses)

    def test_same_reference(self):
        """should modify set of matches"""
        old_matches = self.matches
        player.remove_guesses_from_matches(self.matches, self.guesses)
        case.assertSetEqual(self.matches, old_matches)

    def test_matches_one_guess(self):
        """should remove all guesses from set of matches"""
        first_guess, second_guess = self.guesses
        player.remove_guesses_from_matches(self.matches, {first_guess})
        case.assertSetEqual(self.matches, {second_guess})


def test_get_matches():
    """should correctly find all possible matches given some data"""
    data = {
        "base_suspects": frozenset(BASE_SUSPECTS),
        "match_length": 3,
        "cards": [
            {"suspects": {"pto", "lsl", "jco"}, "match_count": 1},
            {"suspects": {"nnn", "pto", "hbu"}, "match_count": 2},
            {"suspects": {"kca", "pto", "lel"}, "match_count": 2},
            {"suspects": {"kca", "nnn", "lsl"}, "match_count": 0},
        ],
        "previous_guesses": [],
    }
    matches = player.get_matches(**data)
    case.assertSetEqual(matches, {frozenset({"lel", "pto", "hbu"})})


@patch("sys.stdin", NonCallableMock(read=Mock(return_value='{"cards": []}')))
@patch("toac.player.transform_data", return_value={"cards": set()})
@patch("toac.player.get_matches", return_value={frozenset({"hbu", "kca", "pto"})})
def test_main(get_matches, transform_data):
    """should accept input and produce correct output when run from CLI"""
    with redirect_stdout(StringIO()) as out:
        player.main()
        transform_data.assert_called_once_with({"cards": []})
        output = out.getvalue()
        match = set(json.loads(output))
        case.assertSetEqual(match, {"hbu", "kca", "pto"})
