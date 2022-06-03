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


import base64
from collections import OrderedDict, defaultdict
from fabulous.color import bold, green, red, yellow, magenta
import inflect
from itertools import product
import getpass
import hashlib
import networkx as nx
from networkx.algorithms.dag import ancestors
from networkx.algorithms.traversal.depth_first_search import dfs_tree
import numpy
import os
import pathlib
import pkg_resources
import random
import shutil
import stat
import string
import subprocess
import sys
import textwrap

from .pizzazz import *

# this is how random.py does it
def str_to_int(a) :
    a = a.encode()
    a += hashlib.sha512(a).digest()
    a = int.from_bytes(a, 'big')
    a = a%(2**32-1)
    return a


#https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password
import base64
def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()

def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def load_state(fn,key) :
    '''Loads the characters between the save cursor and load cursor ANSI codes
    returns the decode()'ed state stored between those characters, or None if
    the start or stop characters could not be found'''
    with open(fn) as f :
        state = f.read()

    # state is hidden between save cursor and load cursor ansi chars
    try :
        state_start = state.index('\033[s')
        state_end = state.index('\033[u')
        state = state[state_start+3:state_end]
        print(state)
        return eval(decode(key,state))
    except ValueError as e :
        raise e
        # the state could not be successfully decoded, fail
        return None

def save_state(state,fn,key,decoy_text='') :
    with open(fn,'wt') as f :
        encoded = encode(key,repr(state))
        f.write('\033[s')
        f.write(encoded)
        f.write('\033[u')
        f.write(decoy_text)

class PuzzleMaster(object) :
    def __init__(self) :
        self.puzzles = OrderedDict()
    def add(self,puzzle) :
        self.puzzles[puzzle.__name__] = puzzle
    def get(self,puzzle_name) :
        return self.puzzles[puzzle_name]
    def create(self,key) :
        # unlock is the first 'puzzle'
        unlock(key,key).create()
    def unlock(self,key,answer=None) :

        # set the seed and generate the list of answers
        random.seed(key)
        answers = [hex(random.randint(0x10000,0x100000))[2:] for _ in range(len(self.puzzles))]

        # load shadowy figure
        shadowy_figure = os.path.realpath('.shadowy_figure')
        if os.path.exists(shadowy_figure) :
            state = load_state(shadowy_figure,key)
            if state is None : # they messed with the reaper
                print(bold(red('You should have feared the reaper, but you'
                    'messed with him/her/them, and now you will pay the '
                    'ultimate, some might even say terminal, price.')))
                # reset all puzzles
                for puz in self.puzzles :
                    if os.path.exists(puz.name) :
                        shutil.rmtree(puz.name)
                os.remove(shadowy_figure)
        else : 
            state = {}

        if answer is not None :
            if answer == answers[0] : # first unlock

                # create shadowy figure
                fn = pkg_resources.resource_filename('terminal_temple','data/reaper.txt')
                with open(fn,'rt') as f:
                    reaper = f.read()
                save_state(state,shadowy_figure,key,reaper)

            # TODO I was adding logic to unlock all puzzles at once,
            # and recording whether they are solved in state
            if answer in answers:
                index = answers.index(answer)+1
                if index == len(answers) :
                    dazzle()
                    banner()
                    # set the cursor to the end of the terminal
                    move(0,term.height)
                    sys.exit(0)
                puzzle = list(self.puzzles.values())[index]
                puzzle = puzzle(key,None,index)
                puzzle.create()
            else :
                print('Thank you explorer! But our answer princess is in another castle!')

        opened = []
        num_unlocked = 0
        for i, (pid, puz) in enumerate(self.puzzles.items()) :
            puzzles = puz.scan(key,i,'.')
            if puzzles :
                if all([_.solved() for _ in puzzles]) :
                    num_unlocked += 1
                    opened_answer = bold(yellow(answers[i]))
                else :
                    opened_answer = red('LOCKED')
                opened.append((pid,opened_answer))

        if len(opened) == 0 :
            unlock(key,key).run()
        else :
            if num_unlocked == 1 :
                type_texts(['Yes!','He/she/they can be taught!','\n'])
            elif num_unlocked == 3 :
                type_texts(['Hey.',"You're doing great.",'Keep it up.','\n'])
            elif num_unlocked == 6 :
                type_texts(['One more and you get a set of steak knives.','\n'])

            print('Progress:')
            for puz in opened :
                print(*puz)

# each of these puzzles has a class with class, a classy class
class Puzzle(object) :
    def __init__(self,key,path=None,index=0) :
        self.key = key
        self.path = self.name if path is None else path
        self.index = index

        # set the seed and generate the answer for this puzzle
        random.seed(key)
        self.answer = [hex(random.randint(0x10000,0x100000))[2:] for _ in range(index+1)][-1]
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
                'terminal_temple sha {} $@\n'.format(
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

class test_puzzle(Puzzle) :
    def run(self,*args):
        print('this is a test puzzle. hint: the answer is',yellow(self.answer))
    def solved(self):
        return True
#puzzle_d['test_puzzle'] = test_puzzle

# 1
class file_puzzle(Puzzle) :
    def setup(self) :
        with open(os.path.join(self.path,'file.txt'),'wt') as f :
            f.write('')
    def run(self,*args) :
        if self.solved() :
            print('Good job. Your next code is',yellow(self.answer))
            print('You should now return to the parent directory (cd ..) and '
                  'run '+green('./unlock ')+yellow(self.answer))
        else :
            if not os.path.exists('file.txt') :
                print('Oops, file.txt is the missing. We\'ll create it again for ya.')
                self.setup()
            else :
                path = os.path.join(self.path,'file.txt')
                if os.path.exists(path) :
                    content = open(path).read().strip()
                    if content == '' :
                        print('Gotta put the '+green('stuff')+' in the file.txt')
                    else :
                        print('These are not the '+green('stuff')+' you\'re looking for. Try again.')

            print('When you are done, run me again.')

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
    def hint(self):
        print('Write any non-trivial mathematical expression into the file that is equal to the number written in the filename')
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
    def hint(self):
        print('Use a text editor to move the lines of the file around until the full quote appears.')
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
            'vase.txt':'rose',
            'bonnet.txt':'bee'
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
    def hint(self):
        print('Add the correct word as the only text in its corresponding file.')
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

class find_your_pet(Puzzle):
    def init(self) :
        fn = pkg_resources.resource_filename('terminal_temple','data/animuls.fasta')
        with open(fn,'rt') as f:
            pets = []
            curr_pet = [None,'']
            for r in f :
                if r.startswith('>') :
                    if curr_pet[0] :
                        pets.append(curr_pet)
                    curr_pet = [r[1:].strip(),'']
                else :
                    curr_pet[1] += r
        self.pets = pets
        fn = pkg_resources.resource_filename('terminal_temple','data/locations.txt')
        with open(fn,'rt') as f :
            self.locs = [_.strip() for _ in f.readlines()]

        self.pet_id = random.choice(range(len(pets)))
        self.pet_name, self.pet_pic = self.pets[self.pet_id]

        self.dusty_pic = ''
        for i in range(len(self.pet_pic)) :

            if random.random() < 0.1 and self.pet_pic[i] != '\n':
                self.dusty_pic += '.'
            else :
                self.dusty_pic += self.pet_pic[i]

        # let's say on average 3 animuls per location?
        num_locs = int(len(self.pets)/3)
        self.pet_locs = random.choices(range(num_locs),k=len(self.pets))
        locs = random.choices(self.locs,k=num_locs)
        path_tree = nx.random_tree(num_locs,seed=str_to_int(getpass.getuser()+self.key))
        # pick a random root and build a directed tree from it
        self.root = random.choice(range(num_locs))
        self.path_tree = dfs_tree(path_tree,self.root)

    def setup(self) :
        # create directories and put pets in them based on tree
        for node in self.path_tree.nodes :
            path = nx.shortest_path(self.path_tree,source=self.root,target=node)
            # create the directory if necessary
            p = pathlib.Path(*[self.locs[_] for _ in path])
            p.mkdir(exist_ok=True)
            # create text files with the pets in them based on the path leaf
            leaf = path[-1]
            leaf_pet_locs = [i for i,x in enumerate(self.pet_locs) if x==leaf]
            for leaf_pet in leaf_pet_locs :
                pet_name, pet_art = self.pets[leaf_pet]
                with open(p.joinpath('{}.txt'.format(pet_name)),'wt') as f :
                    f.write(pet_art)

    def run(self,*args):
        if self.solved() :
            print('You found your pet {}!'.format(self.pet_name))
            print('With gratitude, he/she/they give you the next code: {}'.format(yellow(self.answer)))
        else :

            if os.path.exists('home.txt') :

                with open('home.txt') as f :
                    home = f.read().strip()
                if home == self.dusty_pic.strip() :
                    print("Wait, that's not your pet! It looks exactly like that dusty old")
                    print("picture you are using to search for him/her/them. You'll have to")
                    print("just get out there and find that {}!".format(magenta(self.pet_name)))
                else :
                    print("Noooooo, that doesn't look like your beloved {}, keep searching!".format(magenta(self.pet_name)))

            else :

                # reset
                if args[0] == 'reset' :
                    # remove home.txt
                    if os.path.exists('home.txt') :
                        os.remove('home.txt')
                    # remove the root
                    if os.path.exists(self.root) :
                        shutil.rmtree(self.root)

                    print(bold(yellow('RESET!')))
                    print()

                print(bold(red('LOST:')))
                print(self.dusty_pic)
                print()
                print('O noes! Your favoritest pet {} has wandered off into a nearby {}!'.format(magenta(self.pet_name),red(self.locs[self.root])))
                print('He/she/they/other preferred pronoun is certainly off on an adventure')
                print('with a very large number of other woke animules. But, surely, your')
                print('beloved {} would like you to go find them and *mv* them back to'.format(magenta(self.pet_name)))
                print('*home.txt*')

                print('Note - if you mess up and create a pet \'orrorshow, you can run '+green('./find_your_pet reset')+' to reset it')

                self.setup()


    def hint(self):
        print('The file *home.txt* in this directory must have exactly the image of your pet')
    def solved(self):
        if not os.path.exists('home.txt') :
            return False
        with open('home.txt') as f :
            home = f.read().strip()
        return home == self.pet_pic.strip()

class dream(Puzzle):
    def init(self) :
        # read in the quote
        fn = pkg_resources.resource_filename('terminal_temple','data/mlk.txt')
        with open(fn,'rt') as f :
            self.text = f.read().upper()

        # create a random character mapping
        chars = string.ascii_uppercase
        repl_chars = random.sample(string.ascii_uppercase,len(chars))
        self.crypto_map = {ord(k):ord(l) for l,k in zip(chars,repl_chars)}

        # shuffle the crypto text
        self.crypto_text = self.text.translate(self.crypto_map)

    def get_envs(self):
        # print out any current env vars defined
        envs = {k:k for k in string.ascii_uppercase}
        for repl in envs :
            env_val = os.environ.get(repl)
            if env_val and env_val != '' and env_val != repl :
                envs[repl] = env_val
        return envs

    def env_repl(self):
        envs = self.get_envs()
        return self.crypto_text.translate(envs)

    def run(self,*args):

        if args[0] == 'reset' :
            for c in string.ascii_uppercase :
                try :
                    os.environ[c] = c
                except Exception as e :
                    pass
            print(bold(white('POOF!')))

        if self.solved() :
            print(bold(magenta(self.text)))
            print('I have a dream.')
            print('It involves the code {}'.format(yellow(self.answer)))
        else :
            print("\"A society's greatest *export*s, to any *env*ironment, is \n"
                  "not the goods and products it produces, but its ideas; its \n"
                  "intellectual and social innovations that change how we think, \n"
                  "and therefore how we live.\"\n- Some dude or lady probably"
                  "\n\n")
            envs = self.get_envs()
            envs_str = []
            for i, (repl, v) in enumerate(sorted(envs.items())) :
                if repl != v :
                    envs_str.append('{}={}'.format(repl,v))
            print('\n'.join(textwrap.wrap('  '.join(envs_str))))
            envs_tr = {ord(k):ord(v) for k,v in envs.items()}
            crypto_text = self.crypto_text.translate(envs_tr)
            for t, c_orig, c_sub in zip(self.text, self.crypto_text, crypto_text) :
                if t == c_sub :
                    print(white(t),end='')
                else :
                    print(red(c_orig),end='')
    def hint(self) :
        print('Define environment variables like, e.g. export S=D, to solve the cryptogram')
        print('If you want to reset all your mappings, run '+bold(white('unset {A..Z}')))
    def solved(self) :
        return self.env_repl().lower() == self.text.lower()

class tiles(Puzzle) :
    def init(self):
        img_fn = pkg_resources.resource_filename('terminal_temple','data/linux.txt')
        with open(img_fn) as f :
            self.img = f.read().strip('\n')
    def setup(self):
        # the image has 45 rows and 78 columns
        # each piece is thus 15 rows by 26 columns for a 3x3
        img_pieces = defaultdict(list)
        for i, line in enumerate(self.img.split('\n')) :
            bin_i = int(i/15)
            for bin_j in range(3):
                img_pieces[(bin_i,bin_j)].append(line[bin_j*26:(bin_j+1)*26])
        # shuffle the values so the bins and pieces are mixed up
        shuffled_pieces = random.sample(list(img_pieces.values()),len(img_pieces))
        img_pieces = {k:v for k,v in zip(img_pieces,shuffled_pieces)}
        # write out the pieces to files
        for k,pieces in img_pieces.items() :
            with open(os.path.join(self.path,'{}{}.txt'.format(*k)),'wt') as f :
                f.write('\n'.join(pieces))
        # rename one of the files
        to_rename = list(img_pieces.keys())[0]
        to_rename_fn = os.path.join(self.path,'{}{}.txt'.format(*to_rename))
        os.rename(to_rename_fn,to_rename_fn+'_borked')
    def reassemble(self):
        # print out the files in a grid
        pieces = {}
        for (i,j) in product(range(3),range(3)) :
            piece_fn = os.path.join(self.path,'{}{}.txt'.format(i,j))
            if os.path.exists(piece_fn) :
                with open(piece_fn) as f :
                    pieces[(i,j)] = f.readlines()
            else : #missing file
                pieces[(i,j)] = (
                        ['.'*26]*4+
                        ['....Ack! Missing {}!..'.format(piece_fn)]+
                        ['.'*26]*10
                       )
        whole = []
        for i in range(45) : # 45 rows
            bin_i = int(i/15)
            whole.append('')
            for j in range(3) : # 3 pieces across
                whole[-1] += pieces[(bin_i,j)][i%15].strip('\n')
            whole[-1] += '\n'

        return ''.join(whole)
    def run(self,*args):
        if self.solved() :
            print(bold(self.img))
            print()
            print('Hold onto your Tux.')
        else :
            if len(args) > 0 and args[0] == 'reset' :
                self.setup()
            print('Aah! No! The puzzle is all messed up! Gotsta put all the pieces back together in the right order!')
            print()
            # print out the files in a grid
            pieces = {}
            for (i,j) in product(range(3),range(3)) :
                piece_fn = os.path.join(self.path,'{}{}.txt'.format(i,j))
                if os.path.exists(piece_fn) :
                    with open(piece_fn) as f :
                        pieces[(i,j)] = f.readlines()
                else : #missing file
                    pieces[(i,j)] = (
                            ['.'*26]*4+
                            ['..Ack! Missing {}!..'.format(piece_fn)]+
                            ['.'*26]*10
                           )
            whole = []
            for i in range(45) : # 45 rows
                bin_i = int(i/15)
                whole.append('')
                for j in range(3) : # 3 pieces across
                    whole[-1] += pieces[(bin_i,j)][i%15].strip('\n')
                    if j != 3 :
                        whole[-1] += '|'

                whole[-1] += '\n'
                if i%15 == 14 and i != 44:
                    whole.append('-'*26+'+'+'-'*26+'+'+'-'*26+'\n')

            print(''.join(whole))

            print('Note - if you mess up and lose one of the pieces, you can run '+green('./tiles reset')+' to reset it')
            print()
    def solved(self):
        return self.img.strip() == self.reassemble().strip()
