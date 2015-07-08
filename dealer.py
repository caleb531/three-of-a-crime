#!/usr/bin/env python3

import argparse
import json
import itertools
import random
import subprocess


MATCH_LENGTH = 3
BASE_SUSPECTS = {'pto', 'nnn', 'jco', 'lel', 'lsl', 'kca', 'hbu'}
NUM_GAMES = 10


def parse_cli_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'programs',
        metavar='program',
        nargs='+',
        help='one or more player programs to execute')

    return parser.parse_args()


def create_deck():

    combinations = itertools.combinations(BASE_SUSPECTS, r=MATCH_LENGTH)
    return list(map(set, combinations))


def reset_deck(deck, discard_deck):

    for card in discard_deck:
        deck.append(card)
    del discard_deck[:]


def reset_data(data):

    del data['cards'][:]


def build_data_from_deck(deck):

    return {
        'base_suspects': list(BASE_SUSPECTS),
        'match_length': MATCH_LENGTH,
        'cards': [],
        'previous_guesses': []
    }


def draw_card(deck, discard_deck):

    card_suspects = deck.pop()
    discard_deck.append(card_suspects)
    return card_suspects


def get_match_count(suspects, real_suspects):

    return len(suspects & real_suspects)


def run_player_program(player, data, real_suspects):

    data_str = json.dumps(data)
    program = subprocess.Popen(
        player['program'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, error = program.communicate(input=data_str.encode('utf-8'))
    program.stdin.close()
    guessed_suspects = set(json.loads(output.decode('utf-8')))
    if guessed_suspects == real_suspects:
        return True
    else:
        return False


def add_card_to_data(data, suspects, match_count):

    data['cards'].append({
        'suspects': list(suspects),
        'match_count': match_count
    })


def get_average_num_rounds(player):
    return player['rounds'] / NUM_GAMES


def run_games_one_player(deck, player):

    random.shuffle(deck)
    data = build_data_from_deck(deck)
    discard_deck = []
    guessed_correctly = False

    real_suspects = draw_card(deck, discard_deck)

    while not guessed_correctly and len(deck) != 0:

        suspects = draw_card(deck, discard_deck)
        match_count = get_match_count(suspects, real_suspects)
        add_card_to_data(data, suspects, match_count)
        guessed_correctly = run_player_program(player, data, real_suspects)

    rounds = len(data['cards'])
    reset_deck(deck, discard_deck)
    reset_data(data)
    return rounds


def run_games_all_players(deck, players):

    for player in players:

        for i in range(NUM_GAMES):

            rounds = run_games_one_player(deck, player)
            if rounds:
                player['rounds'] += rounds

        print(get_average_num_rounds(player))


def create_players(programs):

    players = []

    for program in programs:

        players.append({
            'program': program,
            'rounds': 0
        })

    return players


def main():

    args = parse_cli_args()
    players = create_players(args.programs)
    deck = create_deck()
    run_games_all_players(deck, players)

if __name__ == '__main__':
    main()
