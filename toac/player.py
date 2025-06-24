#!/usr/bin/env python3

import itertools
import json
import sys


# Disregards all suspects that are definitely not matches
def remove_impossible_suspects(cards, base_suspects):
    for card in cards:
        if card["match_count"] == 0:
            for suspect in card["suspects"]:
                # Discarding will never raise KeyError
                base_suspects.discard(suspect)


# Removes guesses from match set to remove possibility of match being a guess
def remove_guesses_from_matches(matches, guesses):
    for guess in guesses:
        matches.discard(guess)


# Returns boolean indicating if combination agrees with all drawn cards
def combination_matches(combination, cards):
    for card in cards:
        # If number of cards in both combination and suspect card does not
        # equal card's match count, card cannot be a match
        if len(combination & card["suspects"]) != card["match_count"]:
            return False
    return True


# Retrieves set of all possible matches for the given sets
def get_matches(cards, base_suspects, match_length, previous_guesses):
    base_suspects = set(base_suspects)
    remove_impossible_suspects(cards, base_suspects)
    combinations = itertools.combinations(base_suspects, r=match_length)
    matches = set()

    for combination in map(frozenset, combinations):
        if combination_matches(combination, cards):
            matches.add(combination)

    remove_guesses_from_matches(matches, previous_guesses)
    return matches


# Transforms JSON data by converting lists (arrays) to sets as appropriate
def transform_data(data):
    data["base_suspects"] = frozenset(data["base_suspects"])
    for card in data["cards"]:
        card["suspects"] = frozenset(card["suspects"])
    data["previous_guesses"] = frozenset(map(frozenset, data["previous_guesses"]))


def main():
    data = json.loads(sys.stdin.read())
    transform_data(data)

    matches = list(get_matches(**data))
    match = list(matches[0])
    print(json.dumps(match), end="")


if __name__ == "__main__":
    main()
