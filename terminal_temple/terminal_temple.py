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

# puzzles:
# 1. must create a file with a specific name that has specific text in it
# 2. a file is created that has a number between 1 and 100 written out in
#    words. The user must add a mathematical expression to the file that
#    evaluates to the value of the named file
# 3. a file is created that has five lines in it that must be put in a
#    specific order
# 4. must match existing words to files with appropriate names
# 5. the executable in the directory prints output of two files randomly
#    interleaved between stdout and stderr, the user must separate the
#    streams into two files with provided names using redirects
# 6. o noes you lost your kitty! she wandered into this scary directory and
#    hasn't been seen again but you are going to go *find* her. this is what
#    she looks like. a directory is created that has a large number of
#    subdirectories that have files in them named after different animals,
#    and one of them has the picture of your kitty. the user is told they
#    need to find their kitty and move her to their house.txt. The unlock
#    script compares the contents of house.txt to the picture of the kitty
# 7. the user is told to define specific environment variables that spell
#    something fun, MADLIBS!
# 8. A short paragraph has had random words replaced with fruits. This
#    passage is not about fruits. The user must replace all the fruits with
#    correct words deduced from context using sed.

### not implemented
# #. must create five files that are unlocked sequentially by adding specific
#    file content in order

import base64
from collections import OrderedDict

from docopt import docopt

from fabulous import debug, utils, image
from fabulous.color import bold, green, red, yellow, magenta

import getpass
import inflect

import math
import random
import stat
import sys
import time

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
    Usage: terminal_temple create <puzzle> <key> [<path>] [<args>...]
                 terminal_temple run <puzzle> <key> <index> [<path>] [<args>...]
                 terminal_temple sha <code> [<args>...]
    '''
    # create <puzzle> with <key> in directory <path>
    # run <puzzle> with <key> located in . or <path> if supplied

    import sys

    args = sys.argv[1:]

    # create new location
    if len(args) == 0 :

        path = get_random_location()

        # unlock is the first 'puzzle'
        puz = unlock(path,path)
        puz.create()

    else :

        args = docopt(main.__doc__)

        if args['sha'] :
            dec = base64.b64decode(args['<code>'].encode()).decode()
            puzzle_name, path, key, index = dec.split()
        else :
            puzzle_name = args['<puzzle>']
            path = args['<path>']
            key = args['<key>']
            index = args['<index>']

        puzzle = puzzle_d.get(puzzle_name)

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
            if len(args['<args>']) > 0 and args['<args>'][0] == 'hint' :
                print(puzzle.hint())
            else :
                puzzle.run(*args['<args>'])

puzzle_d = OrderedDict()

# each of these puzzles has class, and a class, a classy class
class Puzzle(object) :
    def __init__(self,key,path=None,index=0) :
        self.key = key
        self.path = self.name if path is None else path
        self.index = index

        # set the seed and generate the list of answers
        random.seed(getpass.getuser()+self.key)
        self.answers = [hex(random.randint(0x10000,0x100000))[2:] for _ in range(len(puzzle_d))]
        self.answer = self.answers[index]
        self.init()
    def init(self,*args):
        pass

    def create_dir(self,path=None) :

        # create the directory
        if path is None :
            path = self.name
        if not os.path.isdir(path) :
            os.mkdir(path)

        # create the script file
        script_path = os.path.join(path,self.script_name)
        with open(script_path,'wt') as f :
            sha = base64.b64encode(
                '{} {} {} {}'.format(self.name,'.',self.key,self.index).encode()
            )
            f.write(
                'terminal_temple.py sha {} $@\n'.format(
                sha.decode()
                )
            )
        # make script file executable
        os.chmod(script_path,stat.S_IRWXU)

    # by default just create the directory and script file
    def create(self) :
        self.create_dir(self.path)
        self.setup()
    def setup(self):
        pass

    # returns true if the puzzle under self.path is solved
    def check_script_path(self) :
        return os.path.exists(os.path.join(self.path,self.script_name))
    # load looks into self.path and returns true if the directory appears to have
    # this puzzle
    # by default just look to see if the expected script exists
    def load(self) :
        return self.check_script_path()
    def hint(self) :
        return 'NO HINTS 4 U'

    def solved(self) :
        raise Exception('must override the solved() method on subclasses')
    def run(self,index=0) :
        raise Exception('must override the run() method on subclasses')

    # scan looks in the directory provided for directories that can be load()'ed
    @classmethod
    def scan(cls,key,index=0,path='.') :
        puzzles = []
        for fn in os.listdir(path) :
            p = cls(key,fn,index=index)
            if p.load() : # returns true if this path can be loaded as this puzzle
                puzzles.append(p)
        return puzzles
    @property
    def name(self):
        return getattr(self,'_name',type(self).__name__)
    @property
    def script_name(self):
        return getattr(self,'_script_name',type(self).__name__)

################################################################################
# BEHOLD. The puzzles.
class unlock(Puzzle) :
    def solved(self) :
        return False
    def run(self,*args) :

        print('the first answer is',yellow(self.answer))

        if len(args) > 0 :
            answer = args[0]
            if answer in self.answers:
                index = self.answers.index(answer)+1
                if index == len(self.answers) :
                    print('Good job u won woo hoo')
                    sys.exit(0)
                puzzle = list(puzzle_d.values())[index]
                puzzle = puzzle(self.key,None,index)
                puzzle.create()

        print('searching for puzzles:')
        for i, (pid, puz) in enumerate(puzzle_d.items()) :
            if pid == self.name : continue
            puzzles = puz.scan(self.key,i,'.')
            if puzzles :
                answer = self.answers[i] if all([_.solved() for _ in puzzles]) else red('LOCKED')
                print(pid,yellow(answer),puz.scan(self.key,i,'.'))


class test_puzzle(Puzzle) :
    def run(self,*args):
        print('this is a test puzzle. hint: the answer is',yellow(self.answer))
    def solved(self):
        return True
#puzzle_d['test_puzzle'] = test_puzzle

# 1
class file_puzzle(Puzzle) :
    def run(self,*args) :
        if self.solved() :
            print('Good job. Your next code is',yellow(self.answer))
        else :
            print('Gotta put the stuff in the file.txt')
    def hint(self):
        return 'Put the text "stuff" into a file named file.txt'
    def solved(self) :
        path = os.path.join(self.path,'file.txt')
        if os.path.exists(path) :
            if open(path).read().strip() == 'stuff' :
                return True
        return False

# 2
class yay_math(Puzzle):
    def init(self) :
        # pick a random number
        self.x = random.randint(1001,10001)
        # inflect it
        x_str = inflect.engine().number_to_words(self.x)
        x_str = x_str.replace(',','').replace(' ','-')
        self.fn = os.path.join(self.path,'{}.txt'.format(x_str))
    def setup(self) :
        if not os.path.exists(self.fn) :
            open(self.fn,'w').close()
    def run(self,*args) :
        if self.solved() :
            print('Good job. Your next code is',yellow(self.answer))
        else :

            # read in the output from file
            with open(self.fn) as f :
                # remove all white space
                expr_str = ''.join(f.read().split())

            if expr_str == '' :
                msg = 'Your solution is elegant and subtle, but ultimately incorrect.\n'
            else :
                msg = None
                # don't let them have the easy way out
                try :
                    int(expr_str)
                    msg = ('I like your simplicity, but lets have some actual arithmetic '
                                 'plz k?\n')
                except ValueError as e :
                    pass

                if msg is None :
                    try :
                        x = eval(expr_str)
                        if math.isclose(x,self.x) :
                            msg = 'Good job. Your next code is {}'.format(yellow(self.answer))
                    except Exception as e :
                        msg = ('Whoa boy, theres something funky about what is in that '
                                     'file, check your math.\n')
                    else :
                        msg = red('U do math good. W8 no u dont. Try again.\n')

            print(msg)

            print('Write any mathematical expression into the file that is equal to '
                        'the filename.\n')
            print('{}, {}, {}, {}, and {} only plz k?'.format(
                    magenta('numbers'),
                    *[magenta(_) for _ in '+-*/']
                )
            )
    def solved(self):
        with open(self.fn) as f :
            # remove all white space
            expr_str = ''.join(f.read().split())

        # don't let them have the easy way out
        try :
            int(expr_str)
        except ValueError as e :
            try :
                x = eval(expr_str)
                if x == self.x :
                    return True
            except Exception as e :
                pass
        return False

# 3
class reorder(Puzzle):
    def init(self) :
        self.passage = '''\
        Under normal conditions the research
        scientist is not an innovator but a
        solver of puzzles, and the puzzles upon
        which he concentrates are just those which
        he believes can be both stated and
        solved within the existing scientific
        tradition.
        - Thomas Kuhn
        The Structure of Scientific Revolutions, 1962'''
        self.fn = os.path.join(self.path,'passage.txt')
    def setup(self) :
        shuffled = self.passage.split('\n')
        random.shuffle(shuffled)
        with open(self.fn,'wt') as f :
            f.write('\n'.join(shuffled))
    def run(self,*args) :
        if len(args) > 0 and args[0] == 'reset' :
            self.setup()
        with open(self.fn,'r') as f :
            lines = f.read().split('\n')
            for l1, l2 in zip(self.passage.split('\n'),lines) :
                if l1 == l2 :
                    print(l1)
                else :
                    print(''.join(('.',' ')[_==' '] for _ in l1))
        if self.solved() :
            print('\nWisdom is only possessed by the learned. Well done.',yellow(self.answer))
    def solved(self):
        with open(self.fn,'r') as f :
            lines = f.read().split('\n')
            for l1, l2 in zip(self.passage.split('\n'),lines) :
                if l1 != l2 :
                    return False
        return True

# 4
class match(Puzzle):
    def init(self) :
        self.pairs = {
            'barrel.txt':'water',
            'sandwich.txt':'cheese',
            'house.txt':'kitty',
            'mug.txt':'beer',
            'vase.txt':'rose' #TODO I was coming up with one more match
        }
        self.herring = random.choice(['jellyfish','wombat','elbow','peanut',
            'sausage','mouse']
        )
    def setup(self):
        for k in self.pairs :
            # just touch the files
            with open(os.path.join(self.path,k),'wt') : pass
    def run(self,*args) :
        if self.solved() :
            print('Well done, putter of things into their correct containers.')
            print('Your next code is {}'.format(yellow(self.answer)))
        else :
            print('The five containers in this directory have had their contents'
                  'dumped aaaaaaalllllllllll over:\n')
            words = list(self.pairs.values())+[self.herring]
            print(' '.join(str(magenta(_)) for _ in words))
            print('\nPut them back in their correct containers to solve the '
                  'puzzle.\n',
                  'Oh yeah, and you might notice there is one extra word. No '
                  'idea where that one came from.\n')
            print('Progress:')
            for k,v in self.pairs.items() :
                with open(os.path.join(self.path,k)) as f :
                    resp = f.read().strip()
                    if resp == '' :
                        val = '?????'
                    elif resp == v :
                        val = green(v)
                    else :
                        val = red('NOPE')
                
                print('  {}: {}'.format(k,val))

    def solved(self):
        for k,v in self.pairs.items() :
            with open(os.path.join(self.path,k)) as f :
                if f.read().strip() != v :
                    return False
        return True

# 5
class crossed_streams(Puzzle):
    def init(self) :
        pass
    def run(self,*args) :
        pass
    def solved(self):
        return False

class template(Puzzle):
    def init(self) :
        pass
    def run(self,*args) :
        pass
    def solved(self):
        return False

# order
puzzle_d['unlock'] = unlock
puzzle_d['file_puzzle'] = file_puzzle
puzzle_d['yay_math'] = yay_math
puzzle_d['reorder'] = reorder
puzzle_d['match'] = match

if __name__ == '__main__' :

    main()

moai = '''\
                @@@@@*(%%#/,@@@@@                  
              @@/.............#@@@%                
             @(...................,@/              
            @#.....................,/@             
           @@........................,@            
          @@..,....................,..*@           
         @@,,......,&@@@@@@@@@%........,@          
        @@............................,,,@         
       @@,...,,,,,,,,*//(//,,,,,,...,.,,,,@        
      %@//////////#@@@@@@@@@@@&////*,,,,,//@       
      @@#/#@@@@@@@@@@@@@@/&@@@@@@@@@@@@@@@@@       
    @@@@@@@@@@@@@@@@@@@@///@@@@@@@@@@@@@@@@@@@     
    @@.,@///@@@@@@@@///@/,/@%///@@@@@@@//@,.@@     
    @&,,@/,,*/@@@@///,@#,,,@/////@@@@/,,,@,.,@     
    @&,,@......,,,,,.,@/.,,@,...,,,,....,@,.,@     
    @@,,@......,.....,@*..,@,.......,...,&/,,@     
    @@,%@...........,,@/..,@.......,....,,@.,@.    
    @@,@@...........,@/...,@.........,...,@.,@,    
    @@,@%...........,@,...,\@,..........,,@.,@,    
    @@,@/,.........,@/.....,@,........,,,(@#,@,    
    #@,@//,........,@,.....,@@........,,,//@.@@    
    %@,@//,.......,@/.......@@,........,,//@.&@    
    @%#@//........,@,.......,@#.........,,/@.,@,   
    @,@%/........,@/........,@@,.........,/(@,@@   
   @@,@/........,#&,.........,@/..........,/@,,@   
  /@.,@,.......,(@/..........,@@,.........,,@,,@@  
  @@,,@........,@//,,,..,,,,,,/@@..........,&@/@@# 
 #@(,@@........@@@@////////%@@@@(..........,,@@@@@ 
 @@%/@(..........@@@@@@@@@@@@@@.............,@@@@@ 
 @@@@@..........,...........................,@@@%  
  @@@@.......................................,@@   
    @,..............,,,,,,,,,,...............,@@   
   @@...,,,,,,,,,,/////////////,,,,,,,,......,#@@  
  @@,...,,,////(%@@@@@@@@@@@@@(//////(,.......,@@  
  @@....../@@@@@@@@.........@@@@@@@............&@  
 @@,........,(/(,,,,,,,,,,,,,,*//,.........,...,@  
.@@,..........,,///////////#@@@,..............,,@@ 
*@@/,..,...........,,&@@@@@@,.............,,,,,@@@.
 %@@//,,,................................,,,/#@@@@ 
    @@%//,,,,......,...,,............,,,,(/@@@@    
    @@@@@%////,,,,,,,,,,,,,,,,,,,,,,,///@@@@@@@    
    @@////(@@%/////////////////////(@@@@@///#@@    
    @@/////////(@@@@@@@@@@@@@@@@@@@@@#///////@@    
    @@&///,..,,*//(@@@@@@@@@@@@@@(////,..,,//@@    
    @@@///,..,.....,,,//////////,,...,.,,,,/@@@#   
       @@@@@,,,,,...................,,(@@@@@       
            ,@@@@@@@@@@@%#(#&@@@@@@@@@*            
'''
