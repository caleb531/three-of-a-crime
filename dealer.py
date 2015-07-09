#!/usr/bin/env python3

import argparse
import json
import itertools
import random
import subprocess
from multiprocessing import Lock, Process


MATCH_LENGTH = 3
BASE_SUSPECTS = {'pto', 'nnn', 'jco', 'lel', 'lsl', 'kca', 'hbu'}
NUM_GAMES = 100
BASE_DECK = list(
    map(frozenset, itertools.combinations(BASE_SUSPECTS, r=MATCH_LENGTH)))


# Parse command-line arguments passed to dealer program
def parse_cli_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'programs',
        metavar='program',
        nargs='+',
        help='one or more player programs to execute')

    return parser.parse_args()


# Create a game object for storing the current state of the game
def create_game(game_id, players):

    return {
        'winner': None,
        'rounds': None,
        # Each game process must have its own deck in memory
        'deck': BASE_DECK[:],
        'players': players,
        'id': game_id
    }


# Build data object that is eventually passed to each player program
def build_data_object():

    return {
        'base_suspects': list(BASE_SUSPECTS),
        'match_length': MATCH_LENGTH,
        'cards': [],
        'previous_guesses': []
    }


# Draw a suspects card fron the deck
def draw_card(deck, discard_deck):

    card_suspects = deck.pop()
    discard_deck.append(card_suspects)
    return card_suspects


# Retrieve number of suspects in both a suspects card and the eyewitness card
def get_match_count(suspects, real_suspects):

    return len(suspects & real_suspects)


# Pass data object to player program and parse guessed suspects from JSON
def get_player_guess(player, data):

    data_str = json.dumps(data)
    program = subprocess.Popen(
        player['program'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, error = program.communicate(input=data_str.encode('utf-8'))
    program.stdin.close()
    guessed_suspects = set(json.loads(output.decode('utf-8')))
    return guessed_suspects


# Add card data to data object that is to be passed to player program
def add_card_to_data(data, suspects, match_count):

    data['cards'].append({
        'suspects': tuple(suspects),
        'match_count': match_count
    })


# Write to stdout statistics for this game
def print_game_stats(game, lock):

    # "Lock" this logic so that processes can't try to run it concurrently
    with lock:
        print('Game #{}'.format(game['id']))
        print('  Winner: P{}'.format(game['winner']['index']))
        print('  Rounds: {}'.format(game['rounds']))


def run_game(game, lock):

    deck = game['deck']
    discard_deck = []
    random.shuffle(deck)
    data = build_data_object()
    real_suspects = draw_card(deck, discard_deck)

    # Continue taking turns until correct guess is made
    guessed_correctly = False
    while not guessed_correctly:
        for player in game['players']:

            suspects = draw_card(deck, discard_deck)
            match_count = get_match_count(suspects, real_suspects)
            add_card_to_data(data, suspects, match_count)
            # Ask player to guess correct suspects and store its response
            guessed_suspects = get_player_guess(player, data)
            if guessed_suspects == real_suspects:
                # If guess is correct, record winner and end game
                guessed_correctly = True
                game['winner'] = player
                break
            else:
                # If guess is incorrect, record guess and keep playing
                data['previous_guesses'].append(list(guessed_suspects))

    # Always record number of rounds that have elapsed by the end of the game
    game['rounds'] = len(data['cards'])
    print_game_stats(game, lock)


# Start all asynchronous processes
def start_processes(processes):

    for process in processes:
        process.start()


# Wait for all processes to complete before continuing
# This does not affect processes that have already started
def join_processes(processes):

    for process in processes:
        process.join()


# Run all games
def run_games(players):

    processes = []
    lock = Lock()
    games = (create_game(g + 1, players) for g in range(NUM_GAMES))

    for game in games:

        process = Process(target=run_game, args=(game, lock))
        processes.append(process)

    start_processes(processes)
    join_processes(processes)


# Create list of players from the list of player program paths
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
