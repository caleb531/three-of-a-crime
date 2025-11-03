#!/usr/bin/env python3

import json
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, NonCallableMock, patch

import toac.player as player

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
    assert isinstance(data["base_suspects"], frozenset)
    assert isinstance(data["cards"], list)
    for card in data["cards"]:
        assert isinstance(card["suspects"], frozenset)
    for guess in data["previous_guesses"]:
        assert isinstance(guess, frozenset)
    assert isinstance(data["previous_guesses"], frozenset)


def test_remove_impossible_suspects_same_reference():
    """should modify base suspect set"""
    base_suspects = set(BASE_SUSPECTS)
    cards = []
    old_base_suspects = base_suspects
    player.remove_impossible_suspects(cards, base_suspects)
    assert base_suspects == old_base_suspects


def test_remove_impossible_suspects():
    """should remove impossible suspects from base suspect set"""
    base_suspects = set(BASE_SUSPECTS)
    cards = [
        {"suspects": {"pto", "lsl", "jco"}, "match_count": 1},
        {"suspects": {"nnn", "pto", "hbu"}, "match_count": 2},
        {"suspects": {"kca", "pto", "lel"}, "match_count": 2},
        {"suspects": {"kca", "nnn", "lsl"}, "match_count": 0},
    ]
    player.remove_impossible_suspects(cards, base_suspects)
    assert base_suspects == {"pto", "jco", "lel", "hbu"}


def test_remove_impossible_suspects_fail_silently():
    """should not raise exception if suspect has already been removed"""
    base_suspects = set(BASE_SUSPECTS)
    cards = [
        {"suspects": ["lel", "lsl", "kca"], "match_count": 0},
        {"suspects": ["jco", "lsl", "hbu"], "match_count": 1},
        {"suspects": ["kca", "nnn", "pto"], "match_count": 2},
        {"suspects": ["lel", "hbu", "kca"], "match_count": 0},
    ]
    player.remove_impossible_suspects(cards, base_suspects)
    assert base_suspects == {"pto", "jco", "nnn"}


def test_remove_guesses_from_matches_same_reference():
    """should modify set of matches"""
    guesses = {
        frozenset({"kca", "nnn", "hbu"}),
        frozenset({"lsl", "pto", "nnn"}),
    }
    matches = set(guesses)
    old_matches = matches
    player.remove_guesses_from_matches(matches, guesses)
    assert matches == old_matches


def test_remove_guesses_from_matches():
    """should remove all guesses from set of matches"""
    guesses = {
        frozenset({"kca", "nnn", "hbu"}),
        frozenset({"lsl", "pto", "nnn"}),
    }
    matches = set(guesses)
    first_guess, second_guess = guesses
    player.remove_guesses_from_matches(matches, {first_guess})
    assert matches == {second_guess}


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
    assert matches == {frozenset({"lel", "pto", "hbu"})}


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
        assert match == {"hbu", "kca", "pto"}
