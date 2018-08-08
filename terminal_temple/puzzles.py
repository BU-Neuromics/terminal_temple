import base64
from collections import OrderedDict

from fabulous.color import bold, green, red, yellow, magenta

import inflect

import getpass

import os
import pkg_resources
import random
import stat
import string
import sys

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
        random.seed(getpass.getuser()+key)
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
        random.seed(getpass.getuser()+self.key)
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
        pass
    def run(self,*args):
        pass
    def solved(self):
        return False

class dream(Puzzle):
    def init(self) :
        # read in the quote
        with open(pkg_resources.resource_filename('terminal_temple','data/mlk.txt'),'rt') as f :
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


