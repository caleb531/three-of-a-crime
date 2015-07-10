#!/usr/bin/env python3

import argparse
import collections
import json
import itertools
import multiprocessing as mp
import random
import subprocess


MATCH_LENGTH = 3
BASE_SUSPECTS = {'pto', 'nnn', 'jco', 'lel', 'lsl', 'kca', 'hbu'}
BASE_DECK = list(
    map(frozenset, itertools.combinations(BASE_SUSPECTS, r=MATCH_LENGTH)))


# Parse command-line arguments passed to dealer program
def parse_cli_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'num_games',
        metavar='ngames',
        type=int,
        help='the number of games to play')
    parser.add_argument(
        'programs',
        metavar='program',
        nargs='+',
        help='one or more player programs to execute')

    return parser.parse_args()


# Create a game object for storing the current state of the game
def create_game(game_id):

    return {
        'winner': None,
        'rounds': None,
        'id': game_id
    }


# Create a new deck by shallow copying the base deck and shuffling it
def create_deck():

    deck = BASE_DECK[:]
    random.shuffle(deck)
    return deck


# Build data object that is eventually passed to each player program
def build_data_object():

    return {
        'base_suspects': list(BASE_SUSPECTS),
        'match_length': MATCH_LENGTH,
        'cards': [],
        'previous_guesses': []
    }


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
    guessed_suspects = frozenset(json.loads(output.decode('utf-8')))
    return guessed_suspects


# Add card data to data object that is to be passed to player program
def add_card_to_data(data, suspects, match_count):

    data['cards'].append({
        'suspects': tuple(suspects),
        'match_count': match_count
    })


# Write to stdout statistics for this game
def print_game_stats(game, lock):

    # "Lock" this logic so that multiple processes can't run it concurrently
    with lock:
        print('Game #{}'.format(game['id']))
        print('  Winner: P{}'.format(game['winner']))
        print('  Rounds: {}'.format(game['rounds']))


# Run game, record data, and output statistics
def run_game(game_id, players, lock, queue):

    game = create_game(game_id)
    deck = create_deck()
    data = build_data_object()
    real_suspects = deck.pop()

    # Continue taking turns until correct guess is made
    guessed_correctly = False
    while not guessed_correctly:
        for player in players:

            suspects = deck.pop()
            match_count = get_match_count(suspects, real_suspects)
            add_card_to_data(data, suspects, match_count)
            # Ask player to guess correct suspects and store its response
            guessed_suspects = get_player_guess(player, data)
            if guessed_suspects == real_suspects:
                # If guess is correct, record winner and end game
                guessed_correctly = True
                game['winner'] = player['id']
                break
            else:
                # If guess is incorrect, record guess and keep playing
                data['previous_guesses'].append(list(guessed_suspects))

    # Always record number of rounds that have elapsed by the end of the game
    game['rounds'] = len(data['cards'])
    print_game_stats(game, lock)
    queue.put(game)


# Start all asynchronous processes
def start_processes(processes):

    for process in processes:
        process.start()


# A generator which waits for each process to finish
# then "yields" its game object from the queue
def get_games_from_queue(processes, queue):

    for process in processes:
        process.join()
        yield queue.get()


# Print the total number of wins for every player
def print_player_wins(games):

    all_wins = collections.defaultdict(int)
    for game in games:
        all_wins[game['winner']] += 1
    for player_id, player_wins in all_wins.items():
        print('P{} Wins: {}'.format(player_id, player_wins))


# Run all games
def run_games(num_games, players):

    processes = []
    lock = mp.RLock()
    queue = mp.Queue()

    # Run each game asynchronously as a separate process
    for game_id in range(1, num_games + 1):
        process = mp.Process(
            target=run_game, args=(game_id, players, lock, queue))
        processes.append(process)

    start_processes(processes)
    games = get_games_from_queue(processes, queue)
    print_player_wins(games)


# Create list of players from the list of player program paths
def create_players(programs):

    players = []

    for p, program in enumerate(programs):

        players.append({
            'program': program,
            'wins': 0,
            'id': p + 1
        })

    return players


def main():

    args = parse_cli_args()
    players = create_players(args.programs)
    run_games(args.num_games, players)

if __name__ == '__main__':
    main()
