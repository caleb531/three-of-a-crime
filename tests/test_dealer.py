#!/usr/bin/env python3

import io
import json
import subprocess
import sys
import nose.tools as nose
import toac.dealer as dealer
from unittest.mock import ANY, Mock, NonCallableMagicMock, patch


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


@patch('subprocess.Popen', return_value=Mock(
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
    '''should print statistics for each game'''
    game = {'id': 1, 'winner': 2, 'rounds': 3}
    lock = NonCallableMagicMock()
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
@patch('toac.dealer.build_data_object', return_value={
    'base_suspects': [], 'match_length': 3, 'cards': [], 'previous_guesses': []
})
@patch('toac.dealer.get_player_guess', side_effect=[
    {"lsl", "lel", "nnn"}, {"hbu", "nnn", "jco"},
    {"pto", "lel", "nnn"}, {"pto", "hbu", "lel"}
])
def test_run_game(get_player_guess, build_data_object, create_deck,
                  create_game):
    '''should run game with given players, taking turns as necessary'''
    players = [
        {'id': 1, 'wins': 0, 'program': './p1'},
        {'id': 2, 'wins': 0, 'program': './p2'},
        {'id': 3, 'wins': 0, 'program': './p3'},
    ]
    lock = NonCallableMagicMock()
    queue = Mock()
    game = create_game.return_value
    deck = create_deck.return_value
    data = build_data_object.return_value
    dealer.run_game(1, players, lock, queue)
    nose.assert_equal(game['winner'], 1)
    nose.assert_equal(game['rounds'], 4)
    nose.assert_equal(len(data['cards']), 4)
    nose.assert_equal(len(data['previous_guesses']), 3)
    queue.put.assert_called_once_with(game)


def test_start_processes():
    '''should start processes when asked to do so'''
    process1 = Mock()
    process2 = Mock()
    dealer.start_processes((process1, process2))
    process1.start.assert_called_once_with()
    process2.start.assert_called_once_with()


def test_get_games_from_queue():
    '''should yield game when joining respective process'''
    processes = [Mock(), Mock(), Mock()]
    queue = Mock()
    games = dealer.get_games_from_queue(processes, queue)
    for g, game in enumerate(games):
        nose.assert_equal(queue.get.call_count, g + 1)


def test_get_sorted_player_wins():
    '''should sort player wins by greatest number of wins'''
    games = [
        {'id': 1, 'rounds': 3, 'winner': 1},
        {'id': 2, 'rounds': 3, 'winner': 2},
        {'id': 3, 'rounds': 3, 'winner': 2},
        {'id': 4, 'rounds': 3, 'winner': 2},
        {'id': 5, 'rounds': 3, 'winner': 3},
        {'id': 6, 'rounds': 3, 'winner': 3}
    ]
    all_wins = list(dealer.get_sorted_player_wins(games))
    nose.assert_list_equal(all_wins, [
        (2, 3), (3, 2), (1, 1)
    ])


@patch('multiprocessing.RLock')
@patch('multiprocessing.Queue')
@patch('multiprocessing.Process')
def test_run_games(Process, Queue, RLock):
    '''should run every game asynchronously in separate process'''
    players = [{'id': 1, 'wins': 0, 'program': './p1'}]
    num_games = 5
    dealer.run_games(num_games, players)
    nose.assert_equal(Process.call_count, num_games)
    Process.assert_any_call(
        target=dealer.run_game, args=(ANY, players, RLock(), Queue()))
    nose.assert_equal(Process.return_value.start.call_count, 5)
    nose.assert_equal(Process.return_value.join.call_count, 5)


def test_create_players():
    '''should create list of player objects from list of program paths'''
    programs = ['./p1', './p2', './p3']
    players = dealer.create_players(programs)
    for p, (program, player) in enumerate(zip(programs, players)):
        nose.assert_dict_equal(player, {
            'program': program, 'wins': 0, 'id': p + 1
        })


@patch('sys.argv', ['./toac/dealer.py', '10', './p1', './p2', './p3'])
@patch('toac.dealer.run_games')
def test_main(run_games):
    '''should run dealer program when executed directly'''
    programs = sys.argv[2:]
    players = dealer.create_players(programs)
    dealer.main()
    run_games.assert_called_once_with(10, players)
