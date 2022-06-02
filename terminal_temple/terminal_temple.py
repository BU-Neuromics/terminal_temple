#!/usr/bin/env python3

# create directory with some randomized name
# inside that directory is an executable file named 'unlock'
# the name of the parent directory is the random seed
# used to generate all subsequent keys and puzzles

# running ./unlock prints out some usage, including a
# simple puzzle to provide a key, some word

# the user is instructed to type ./unlock <key>
# which creates a new directory named something with
# another executable inside that provides instructions on
# a new puzzle
# the solution to the puzzle is a new key to give to
# the ./unlock script in the parent directory

# every time the user provides a correct key a file treasure.txt
# is created that has an ascii art of something which is the
# final key to beat the game


import base64

from docopt import docopt

from fabulous import debug, utils, image
from fabulous.color import bold, green, red, yellow, magenta

import math
import pkg_resources
import random
import stat
import sys
import time

from terminal_temple.puzzles import *
from terminal_temple.pizzazz import *

# importlib requires python >=3.1
import importlib
import os

def code_to_file(code,cfile) :
    if isinstance(code,str) :
        code = compile(code,'<string>','exec')

    bytecode = importlib._bootstrap_external._code_to_bytecode(
        code,
        time.time(),
        1
    )

    importlib._bootstrap_external._write_atomic(
        cfile,
        bytecode,
        stat.S_IRWXU
    )
    os.chmod(cfile,stat.S_IRWXU)

locations = [
    (
        'mysterious','quixotic','hidden','wonderous','splendiferous','murky',
        'creepy','moss-covered','dank','voluminous','cavernous','dazzling',
        'sparkly','decrepit','ancient','noisome'
    ),
    (
        'cave','crypt','temple','ruins','cavern','tomb','mausoleum','pyramid',
        'ziggurat','stupa','lighthouse','colosseum'
    )
]
def get_random_location() :
    return '_'.join(
        (
            random.choice(locations[0]),
            random.choice(locations[1])
        )
    )

def main() :
    '''
    Usage: terminal_temple create <puzzle> <key> [<path>] [<guess>] [<args>...]
                 terminal_temple run <puzzle> <key> <index> [<path>] [<guess>] [<args>...]
                 terminal_temple sha <code> [<guess>] [<args>...]
    '''
    # create <puzzle> with <key> in directory <path>
    # run <puzzle> with <key> located in . or <path> if supplied

    args = sys.argv[1:]

    puz_mas = PuzzleMaster()

    # order of puzzles
    puzzle_order = [
        unlock,
        file_puzzle,
        yay_math,
        reorder,
        match,
        find_your_pet,
        dream,
        tiles,
    ]
    for puz in puzzle_order :
        puz_mas.add(puz)

    # create new puzzle location
    if len(args) == 0 :
        img = image.Image(
                pkg_resources.resource_filename('terminal_temple','data/head.png')
        )
        # python 2v3 issue
        image.basestring = str
        img.resize(min(term.width,int(2*term.height*img.size[0]/term.width)))

        special = {
                '<head.png>':img,
                '<terminal_temple>':(
                    str(text.Text('terminal',color=banner_color,skew=5,shadow=True))+
                    str(text.Text('temple',color=banner_color,skew=5,shadow=True))
                    )
                }

        path = get_random_location()

        try :

            script_fn = pkg_resources.resource_filename('terminal_temple','data/greeting.txt')
            with open(script_fn) as f :
                for line in f :
                    if line.strip() in special :
                        print('\n')
                        print(special[line.strip()])
                        sleep(5)
                    else :
                        type_text('\n'+eval(line),speed=0.04)
                        sleep(1)

        except KeyboardInterrupt as e :
            type_text('\nOk ok fine impatient pants here\'s your puzzle directory geez: '+magenta(path)+'\n')

        puz_mas.create(path)

    # otherwise we're running a puzzle op
    else :

        args = docopt(main.__doc__)

        # the current puzzle state is obfuscated with bas64
        if args['sha'] :
            dec = base64.b64decode(args['<code>'].encode()).decode()
            puzzle_name, path, key, index = dec.split()
        else :
            puzzle_name = args['<puzzle>']
            path = args['<path>']
            key = args['<key>']
            index = args['<index>']
            if not index :
                index = 0

        # unlock is a special case
        if puzzle_name == 'unlock' :
            puz_mas.unlock(key,args.get('<guess>'))

        else :
            puzzle = puz_mas.get(puzzle_name)

            if puzzle is None :
                print('No puzzle with that name:',args[0])
                sys.exit(1)

            if not path :
                path = '.'
            puzzle = puzzle(key,path,index=int(index))

            # create branch is mostly for debugging/dev
            if args['create'] :
                key = os.path.split(os.getcwd())[1]
                puzzle.create()
            else :
                if not puzzle.load() :
                    raise Exception('Error scanning path {} for puzzle {} and key {}, aborting'.format(
                        path,puzzle_name,key
                    ))
                if args['<guess>'] == 'hint' :
                    print(puzzle.hint())
                else :
                    puzzle.run(*[args['<guess>']]+args['<args>'])


if __name__ == '__main__' :

    main()
