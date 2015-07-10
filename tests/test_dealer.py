#!/usr/bin/env python3

import contextlib
import io
import json
import subprocess
import nose.tools as nose
import toac.dealer as dealer
from unittest.mock import MagicMock, Mock, NonCallableMock, patch


def test_create_game():
    '''should create game object with correct properties'''
    nose.assert_dict_equal(
        dealer.create_game(3), {'id': 3, 'winner': None, 'rounds': None})


def test_create_deck():
    '''should create shuffled deck'''
    deck = dealer.create_deck()
    nose.assert_is_instance(deck, list)
    nose.assert_not_equal(deck, dealer.BASE_DECK)
    nose.assert_set_equal(set(deck), set(dealer.BASE_DECK))


def test_build_data_object():
    '''should create correct data object to pass to player'''
    data = dealer.build_data_object()
    nose.assert_equal(data, {
        'base_suspects': list(dealer.BASE_SUSPECTS),
        'match_length': 3,
        'cards': [],
        'previous_guesses': []
    })


def test_get_match_count():
    '''should calculate correct number of suspects shared by two cards'''
    real_suspects = {'hbu', 'pto', 'lel'}
    suspects = {'lel', 'pto', 'nnn'}
    nose.assert_equal(dealer.get_match_count(suspects, real_suspects), 2)


@patch('subprocess.Popen', return_value=MagicMock(
    communicate=Mock(return_value=(b'["hbu", "lel", "pto"]', None))))
def test_get_player_guess(popen):
    '''should ask user to guess correct suspects and store their guess'''
    player = {'id': 1, 'program': './p1', 'wins': 0}
    data = {'base_suspects': [], 'match_length': 3, 'cards': [],
            'previous_guesses': []}
    guessed_suspects = dealer.get_player_guess(player, data)
    popen.assert_called_once_with(
        player['program'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    popen.return_value.communicate.assert_called_once_with(
        input=json.dumps(data).encode('utf-8'))
    nose.assert_set_equal(
        guessed_suspects, {'hbu', 'lel', 'pto'})


def test_add_card_to_data():
    data = {'cards': []}
    suspects = {'lel', 'pto', 'nnn'}
    match_count = 2
    dealer.add_card_to_data(data, suspects, match_count)
    nose.assert_equal(len(data['cards']), 1)
    nose.assert_list_equal(data['cards'], [{
        'suspects': tuple(suspects),
        'match_count': match_count
    }])


def test_print_game_stats():
    game = {'id': 1, 'winner': 2, 'rounds': 3}
    lock = MagicMock()
    dealer.print_game_stats(game, lock)
    lock.__enter__.assert_called_once_with()
    lock.__exit__.assert_called_once_with(None, None, None)


@patch('toac.dealer.create_game', return_value={
    'id': 1, 'winner': None, 'rounds': None
})
@patch('toac.dealer.create_deck', return_value=[
    {'pto', 'lsl', 'jco'}, {'nnn', 'pto', 'hbu'}, {'kca', 'pto', 'lel'},
    {'kca', 'nnn', 'lsl'}, {'lel', 'pto', 'hbu'}
])
@patch('toac.dealer.get_player_guess', side_effect=[
    {"lsl", "lel", "nnn"}, {"hbu", "nnn", "jco"},
    {"pto", "lel", "nnn"}, {"pto", "hbu", "lel"}
])
def test_run_game(get_player_guess, create_deck, create_game):
    players = [
        {'id': 1, 'wins': 0, 'program': './p1'},
        {'id': 2, 'wins': 0, 'program': './p2'},
        {'id': 3, 'wins': 0, 'program': './p3'},
        {'id': 4, 'wins': 0, 'program': './p4'},
        {'id': 5, 'wins': 0, 'program': './p5'}
    ]
    lock = MagicMock()
    queue = MagicMock()
    dealer.run_game(1, players, lock, queue)
    game = create_game.return_value
    nose.assert_equal(game['winner'], 4)
