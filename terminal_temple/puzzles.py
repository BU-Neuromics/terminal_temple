import base64
from collections import OrderedDict, defaultdict
from fabulous.color import bold, green, red, yellow, magenta
import inflect
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
import stat
import string
import sys

# this is how random.py does it
def str_to_int(a) :
    a = a.encode()
    a += hashlib.sha512(a).digest()
    a = int.from_bytes(a, 'big')
    a = a%(2**32-1)
    return a

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
        seed = numpy.random.RandomState(str_to_int(getpass.getuser()+key))
        random.seed(seed)
        answers = [hex(random.randint(0x10000,0x100000))[2:] for _ in range(len(self.puzzles))]

        if answer is not None :
            if answer in answers:
                index = answers.index(answer)+1
                if index == len(answers) :
                    print('Good job u won woo hoo')
                    sys.exit(0)
                puzzle = list(self.puzzles.values())[index]
                puzzle = puzzle(key,None,index)
                puzzle.create()
            else :
                print('Thank you explorer! But our answer princess is in another castle!')

        opened = []
        for i, (pid, puz) in enumerate(self.puzzles.items()) :
            puzzles = puz.scan(key,i,'.')
            if puzzles :
                opened_answer = answers[i] if all([_.solved() for _ in puzzles]) else red('LOCKED')
                opened.append((pid,yellow(answer),opened_answer,puz.scan(key,i,'.')))

        if len(opened) == 0 :
            unlock(key,key).run()
        else :
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
        #self.seed = numpy.random.RandomState(str_to_int(getpass.getuser()+self.key))
        #random.seed(self.seed)
        random.seed(str_to_int(getpass.getuser()+self.key))
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
            locs = [_.strip() for _ in f.readlines()]
        # let's say on average 3 animuls per location?
        num_locs = int(len(pets)/3)
        pet_locs = random.choices(range(num_locs),k=len(pets))
        self.locs = locs = random.choices(locs,k=num_locs)
        path_tree = nx.random_tree(num_locs,seed=str_to_int(getpass.getuser()+self.key))
        # create directories and put pets in them based on tree
        self.root = random.choice(range(num_locs))
        path_tree = dfs_tree(path_tree,self.root)
        for node in path_tree.nodes :
            path = nx.shortest_path(path_tree,source=self.root,target=node)
            # create the directory if necessary
            p = pathlib.Path(*[locs[_] for _ in path])
            p.mkdir(exist_ok=True)
            # create text files with the pets in them based on the path leaf
            leaf = path[-1]
            leaf_pet_locs = [i for i,x in enumerate(pet_locs) if x==leaf]
            for leaf_pet in leaf_pet_locs :
                pet_name, pet_art = pets[leaf_pet]
                with open(p.joinpath('{}.txt'.format(pet_name)),'wt') as f :
                    f.write(pet_art)
        self.pet_id = random.choice(range(len(pets)))
        self.pet_name, self.pet_pic = self.pets[self.pet_id]

        self.dusty_pic = ''
        for i in range(len(self.pet_pic)) :
            if random.random() < 12/len(self.pet_pic) :
                self.dusty_pic += '.'
            else :
                self.dusty_pic += self.pet_pic[i]

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
                    print("just get out there and find that ****ing {}!".format(self.pet_name))
                else :
                    print("Noooooo, that doesn't look like your beloved {}, keep searching!".format(self.pet_name))

            print(bold(red('LOST:')))
            print(self.dusty_pic)
            print()
            print('O noes! Your favoritest pet {} has wandered off into a nearby {}!'.format(self.pet_name,self.locs[self.root]))
            print('He/she/they/other preferred pronouns is certainly off on an adventure')
            print('with a very large number of other woke animules. But, surely, your')
            print('beloved {} would like you to go find them and *mv* them back to'.format(self.pet_name))
            print('*home.txt*')
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
            self.text = f.read()
        chars = sorted(list(set(self.text.lower()).intersection(string.ascii_lowercase)))
        repl_chars = random.sample(string.ascii_uppercase,len(chars))
        self.crypto_map = {k:l for l,k in zip(chars,repl_chars)}
    def get_envs(self):
        # print out any current env vars defined
        envs = {}
        for repl in self.crypto_map :
            env_val = os.environ.get(repl)
            if env_val :
                envs[repl] = env_val
        return envs

    def env_repl(self):
        envs = self.get_envs()
        # substitute based on the vars from above
        crypto_text = self.text.lower()
        for repl, char in self.crypto_map.items() :
            crypto_text = crypto_text.replace(char,repl)
            # now substitue back
            if repl in envs :
                crypto_text = crypto_text.replace(repl,envs[repl])
        return crypto_text
    def run(self):
        crypto_text = self.env_repl()
        if self.solved() :
            print(bold(magenta(self.text)))
            print('I have a dream.')
            print('It involves the code {}'.format(yellow(self.answer)))
        else :
            envs = self.get_envs()
            envs_str = []
            for i, (repl, v) in enumerate(sorted(envs.items())) :
                envs_str.append('{}={}'.format(repl,v))
                if i%5 == 4 :
                    envs_str.append('\n')
            print('  '+'  '.join(envs_str))
            print(red(crypto_text))
    def solved(self) :
        return self.env_repl().lower() == self.text.lower()

class template(Puzzle):
    def init(self) :
        pass
    def run(self,*args) :
        pass
    def solved(self):
        return False


