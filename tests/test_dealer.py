#!/usr/bin/env python3

import contextlib
import io
import json
import nose.tools as nose
import toac.dealer as dealer
from unittest.mock import MagicMock, Mock, NonCallableMock, patch


def test_create_game():
    '''should create game object with correct properties'''
    nose.assert_dict_equal(dealer.create_game(3), {
        'id': 3,
        'winner': None,
        'rounds': None
    })


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
    game = {
        'id': 1,
        'winner': 2,
        'rounds': 3
    }
    lock = MagicMock()
    dealer.print_game_stats(game, lock)
    lock.__enter__.assert_called_once_with()
    lock.__exit__.assert_called_once_with(None, None, None)
