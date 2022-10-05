#!/usr/bin/env python3

import copy
import json
import subprocess
import sys
import toac.dealer as dealer
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import ANY, Mock, NonCallableMagicMock, patch


case = unittest.TestCase()


def test_create_game():
    """should create game object with correct properties"""
    case.assertDictEqual(
        dealer.create_game(3), {'id': 3, 'winner': None, 'rounds': 0})


def test_create_deck():
    """should create shuffled deck"""
    deck = dealer.create_deck()
    case.assertIsInstance(deck, list)
    case.assertNotEqual(deck, dealer.BASE_DECK)
    case.assertSetEqual(set(deck), set(dealer.BASE_DECK))


def test_build_data_object():
    """should create correct data object to pass to player"""
    data = dealer.build_data_object()
    case.assertEqual(data, {
        'base_suspects': list(dealer.BASE_SUSPECTS),
        'match_length': 3,
        'cards': [],
        'previous_guesses': []
    })


def test_get_match_count():
    """should calculate correct number of suspects shared by two cards"""
    real_suspects = {'hbu', 'pto', 'lel'}
    suspects = {'lel', 'pto', 'nnn'}
    case.assertEqual(dealer.get_match_count(suspects, real_suspects), 2)


@patch('subprocess.Popen', return_value=Mock(
    communicate=Mock(return_value=(b'["hbu", "lel", "pto"]', None))))
def test_get_player_guess(popen):
    """should ask user to guess correct suspects and store their guess"""
    player = {'id': 'P1', 'program': './p1', 'wins': 0}
    data = {'base_suspects': [], 'match_length': 3, 'cards': [],
            'previous_guesses': []}
    guessed_suspects = dealer.get_player_guess(player, data)
    popen.assert_called_once_with(
        player['program'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    popen.return_value.communicate.assert_called_once_with(
        input=json.dumps(data, separators=(',', ':')).encode('utf-8'))
    case.assertSetEqual(
        guessed_suspects, {'hbu', 'lel', 'pto'})


def test_add_card_to_data():
    data = {'cards': []}
    suspects = {'lel', 'pto', 'nnn'}
    match_count = 2
    dealer.add_card_to_data(data, suspects, match_count)
    case.assertEqual(len(data['cards']), 1)
    case.assertListEqual(data['cards'], [{
        'suspects': tuple(suspects),
        'match_count': match_count
    }])


@patch('toac.dealer.print')
def test_print_game_stats(print):
    """should print statistics for each game"""
    game = {'id': 1, 'winner': 2, 'rounds': 3}
    lock = NonCallableMagicMock()
    dealer.print_game_stats(game, lock)
    lock.__enter__.assert_called_once_with()
    lock.__exit__.assert_called_once_with(None, None, None)


class TestRunGame(object):
    """run_game should behave as expected in all cases"""

    PLAYERS = [
        {'id': 1, 'wins': 0, 'program': './p1'},
        {'id': 2, 'wins': 0, 'program': './p2'},
        {'id': 3, 'wins': 0, 'program': './p3'},
    ]
    GAME = {'id': 1, 'winner': None, 'rounds': 0}
    DECK = [
        {'pto', 'lsl', 'jco'}, {'nnn', 'pto', 'hbu'}, {'kca', 'pto', 'lel'},
        {'kca', 'nnn', 'lsl'}, {'lel', 'pto', 'hbu'}
    ]
    DATA = {
        'base_suspects': [],
        'match_length': 3,
        'cards': [],
        'previous_guesses': []
    }
    GUESSES = [
        {"lsl", "lel", "nnn"}, {"hbu", "nnn", "jco"},
        {"pto", "lel", "nnn"}, {"pto", "hbu", "lel"}
    ]

    def setUp(self):
        self.lock = NonCallableMagicMock()

    @patch('toac.dealer.create_game', return_value=copy.deepcopy(GAME))
    @patch('toac.dealer.create_deck', return_value=copy.deepcopy(DECK))
    @patch('toac.dealer.build_data_object', return_value=copy.deepcopy(DATA))
    @patch('toac.dealer.get_player_guess', side_effect=copy.deepcopy(GUESSES))
    def test_run_game(self, get_player_guess, build_data_object, create_deck,
                      create_game):
        """should run game with given players, taking turns as necessary"""
        game = create_game.return_value
        data = build_data_object.return_value
        with redirect_stdout(StringIO()):
            dealer.run_game(1, self.PLAYERS, self.lock)
        case.assertEqual(game['winner'], 1)
        case.assertEqual(game['rounds'], 4)
        case.assertEqual(len(data['cards']), 4)
        case.assertEqual(len(data['previous_guesses']), 3)

    @patch('toac.dealer.create_game', return_value=copy.deepcopy(GAME))
    @patch('toac.dealer.create_deck', return_value=copy.deepcopy(DECK))
    @patch('toac.dealer.build_data_object', return_value=copy.deepcopy(DATA))
    @patch('toac.dealer.get_player_guess', return_value=[GUESSES[1]])
    def test_exhaust_deck(self, get_player_guess, build_data_object,
                          create_deck, create_game):
        """should fail gracefully if deck is exhausted during gameplay"""
        game = create_game.return_value
        data = build_data_object.return_value
        with redirect_stdout(StringIO()):
            dealer.run_game(1, self.PLAYERS, self.lock)
        case.assertEqual(game['winner'], None)
        case.assertEqual(game['rounds'], 4)
        case.assertEqual(len(data['cards']), 4)
        case.assertEqual(len(data['previous_guesses']), 3)

    @patch('toac.dealer.create_game', return_value=copy.deepcopy(GAME))
    @patch('toac.dealer.create_deck', return_value=copy.deepcopy(DECK))
    @patch('toac.dealer.build_data_object', return_value=copy.deepcopy(DATA))
    @patch('toac.dealer.get_player_guess', side_effect=ValueError)
    def test_invalid_json(self, get_player_guess, build_data_object,
                          create_deck, create_game):
        """should silently fail when invalid JSON produces ValueError"""
        game = create_game.return_value
        data = build_data_object.return_value
        with redirect_stdout(StringIO()):
            dealer.run_game(1, self.PLAYERS, self.lock)
        case.assertEqual(game['winner'], None)
        case.assertEqual(game['rounds'], 1)
        case.assertEqual(len(data['cards']), 1)
        case.assertEqual(len(data['previous_guesses']), 0)


def test_get_finished_games():
    """should yield game when joining respective process"""
    processes = [Mock(), Mock(), Mock()]
    games = dealer.get_finished_games(processes)
    for game, process in zip(games, processes):
        case.assertEqual(process.get.call_count, 1)


def test_get_sorted_player_wins():
    """should sort player wins by greatest number of wins"""
    games = [
        {'id': 1, 'rounds': 3, 'winner': 'P1'},
        {'id': 2, 'rounds': 3, 'winner': 'P2'},
        {'id': 3, 'rounds': 3, 'winner': 'P2'},
        {'id': 4, 'rounds': 3, 'winner': 'P2'},
        {'id': 5, 'rounds': 3, 'winner': 'P3'},
        {'id': 6, 'rounds': 3, 'winner': 'P3'}
    ]
    all_wins = list(dealer.get_sorted_player_wins(games))
    case.assertListEqual(all_wins, [
        ('P2', 3), ('P3', 2), ('P1', 1)
    ])


@patch('toac.dealer.print')
def test_print_player_wins(print):
    """should print player wins, only counting games with winners"""
    games = [
        {'id': 1, 'winner': 'P2', 'rounds': 4},
        {'id': 2, 'winner': 'P3', 'rounds': 3},
        {'id': 3, 'winner': 'P3', 'rounds': 3},
        {'id': 4, 'winner': 'P1', 'rounds': 4},
        {'id': 5, 'winner': None, 'rounds': 34}
    ]
    dealer.print_player_wins(games)
    case.assertEqual(print.call_count, 3)
    print.assert_any_call('P3 Wins: 2')
    print.assert_any_call('P2 Wins: 1')
    print.assert_any_call('P1 Wins: 1')


@patch('multiprocessing.pool.Pool.apply_async')
def test_run_games_mock_pool(apply_async):
    """should run every game asynchronously in separate (mocked) pool"""
    players = [{'id': 1, 'wins': 0, 'program': './toac/player.py'}]
    num_games = 5
    with redirect_stdout(StringIO()):
        dealer.run_games(num_games, players)
    case.assertEqual(apply_async.call_count, num_games)
    apply_async.assert_any_call(
        dealer.run_game, args=(1, players, ANY))
    case.assertEqual(apply_async.return_value.get.call_count, 5)


def test_create_players():
    """should create list of player objects from list of program paths"""
    programs = ['./p1', './p2', './p3']
    players = dealer.create_players(programs)
    for p, (program, player) in enumerate(zip(programs, players)):
        case.assertDictEqual(player, {
            'program': program, 'wins': 0, 'id': 'P{}'.format(p + 1)
        })


@patch('sys.argv', ['./toac/dealer.py', '10', './p1', './p2', './p3'])
@patch('toac.dealer.run_games')
def test_main(run_games):
    """should run dealer program when executed directly"""
    programs = sys.argv[2:]
    players = dealer.create_players(programs)
    with redirect_stdout(StringIO()):
        dealer.main()
    run_games.assert_called_once_with(10, players)
