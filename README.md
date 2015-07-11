# Three of a Crime Solver

*Copyright 2015 Caleb Evans*  
*Released under the MIT license*

[![Build
Status](https://travis-ci.org/caleb531/three-of-a-crime.svg?branch=master)](https://travis-ci.org/caleb531/three-of-a-crime)
[![Coverage
Status](https://coveralls.io/repos/caleb531/three-of-a-crime/badge.svg?branch=master)](https://coveralls.io/r/caleb531/three-of-a-crime?branch=master)

This project was created and named for the Gameright game, [Three of a
Crime](http://www.gamewright.com/gamewright/index.php?page=game&section=games&show=214).
To understand the purpose of this project, one must first understand how the
game works.

## Gameplay

![Three of a
Crime](http://www.gamewright.com/gamewright/Images/Games/GAMEWRIGHT-236.jpg)

Seven suspects for an unmentioned crime are distributed among 35 cards
representing all possible 3-suspect combinations. One player is designated as
the eyewitness, and thus draws the first card in the deck. The three suspects on
this card are the suspects responsible for the crime.

The other players (who are, implicitly, the game's detectives) take turns
drawing cards from the deck. For every card that is drawn, the eyewitness player
places a number tile next to the card indicating how many suspects on said card
match the suspects on the eyewitness card (this number can be 0, 1, or 2).

As cards are drawn and number tiles are placed, players must use deductive
reasoning to determine which three suspects are on the eyewitness card. The
first player to guess correctly wins the game.

## Purpose of the project

The purpose of this project was to design a program which, given some input
representing the state of the game, could accurately guess the correct suspects
on the eyewitness card. A Python implementation of such a dealer program can be
found at `toac/player.py`.

However, in order to truly test the intelligence of the player program, a dealer
progam was designed to simulate actual gameplay. This dealer program can be
found at `toac/dealer.py`. To run the dealer program, simply invoke the program
executable with the number of games to play, followed by the paths to two or
more player programs.

```
./toac/dealer.py 10 ./toac/player.py ./toac/player.py
```

The dealer program will then output statistics for each game, including winner
and rounds elapsed. Once all games have finished, the program will output the
total number of wins for each player, sorted by most wins.

## Creating your own player

To create your own player program, you must write a program which follows a few
simple rules:

### Accepting input

The program must accept a string of JSON data via stdin. See the provided
example JSON file, which can be found at `toac/example.py`, for the
structure/semantics of the data that .

### Returning output

After receiving game data as input, the program must output a JSON array
containing the three suspects it thinks are on the eyewitness card. The order of
this array does not matter, and any superfluous whitespace is simply ignored by
the dealer program.

An example of such output might be `["hbu", "lel", "pto"]`, where each item
represents one of the seven suspects in the game. Naturally, the value of each
item must exist within the `base_suspects` array apart of the input JSON.

### Incorrect guesses

Please also note that while you should strive for your program to produce an
accurate guess, the dealer program will not penalize player programs for
incorrect guesses.

### Executing the program

Every player program must be marked as executable, and the dealer program will
expect such to be the case. To mark your program as executable, use the UNIX
`chmod` utility:

```
chmod +x ./toac/myplayer.py
```
