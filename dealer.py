#!/usr/bin/env python3

import argparse
import json
import itertools
import multiprocessing
import random
import subprocess


MATCH_LENGTH = 3
BASE_SUSPECTS = {'pto', 'nnn', 'jco', 'lel', 'lsl', 'kca', 'hbu'}
NUM_GAMES = 100
BASE_DECK = list(
    map(frozenset, itertools.combinations(BASE_SUSPECTS, r=MATCH_LENGTH)))


def parse_cli_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'programs',
        metavar='program',
        nargs='+',
        help='one or more player programs to execute')

    return parser.parse_args()


def reset_deck(deck, discard_deck):

    for card in discard_deck:
        deck.append(card)
    del discard_deck[:]


def create_game(game_id, players):

    return {
        'winner': None,
        'rounds': None,
        'deck': BASE_DECK[:],
        'players': players,
        'id': game_id
    }


def reset_data(data):

    del data['cards'][:]


def build_data_object():

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


def get_player_guess(player, data):

    data_str = json.dumps(data)
    program = subprocess.Popen(
        player['program'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, error = program.communicate(input=data_str.encode('utf-8'))
    program.stdin.close()
    guessed_suspects = set(json.loads(output.decode('utf-8')))
    return guessed_suspects


def add_card_to_data(data, suspects, match_count):

    data['cards'].append({
        'suspects': tuple(suspects),
        'match_count': match_count
    })


def get_average_num_rounds(player):
    return player['rounds'] / NUM_GAMES


def run_game(game, lock):

    deck = game['deck']
    discard_deck = []
    random.shuffle(deck)
    data = build_data_object()
    guessed_correctly = False

    real_suspects = draw_card(deck, discard_deck)

    while not guessed_correctly:

        for player in game['players']:

            suspects = draw_card(deck, discard_deck)
            match_count = get_match_count(suspects, real_suspects)
            add_card_to_data(data, suspects, match_count)
            guessed_suspects = get_player_guess(player, data)
            if guessed_suspects == real_suspects:
                guessed_correctly = True
                game['winner'] = player
                break
            else:
                data['previous_guesses'].append(list(guessed_suspects))

    game['rounds'] = len(data['cards'])
    reset_deck(deck, discard_deck)
    reset_data(data)

    # "Lock" this logic so that processes can't try to run it concurrently
    with lock:
        print('Game #{}'.format(game['id']))
        print('  Winner: P{}'.format(game['winner']['index']))
        print('  Rounds: {}'.format(game['rounds']))


# Start all asynchronous processes
def start_processes(processes):

    for process in processes:
        process.start()


# Wait for all processes to complete
def join_processes(processes):

    for process in processes:
        process.join()


def run_games(players):

    processes = []
    games = (create_game(g + 1, players) for g in range(NUM_GAMES))
    lock = multiprocessing.Lock()

    for game in games:

        process = multiprocessing.Process(
            target=run_game, args=(game, lock))
        processes.append(process)

    start_processes(processes)
    join_processes(processes)


def create_players(programs):

    players = []

    for p, program in enumerate(programs):

        players.append({
            'program': program,
            'rounds': 0,
            'index': p + 1
        })

    return players


def main():

    args = parse_cli_args()
    players = create_players(args.programs)
    run_games(players)

if __name__ == '__main__':
    main()
