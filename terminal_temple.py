basestring = str

from fabulous import debug, utils, image

import stat
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

def main() :

  import sys

  args = sys.argv[1:]

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
  # #. must create a file with a specific name that has specific text in it
  # #. a file is created that has a number between 1 and 100 written out in
  #    words. The user must add a mathematical expression to the file that
  #    evaluates to the value of the named file
  # #. a file is created that has five lines in it that must be put in a
  #    specific order
  # #. must create five files that are unlocked sequentially by adding specific
  #    file content in order
  # #. the executable in the directory prints output of two files randomly
  #    interleaved between stdout and stderr, the user must separate the
  #    streams into two files with provided names using redirects
  # #. o noes you lost your kitty! she wandered into this scary directory and
  #    hasn't been seen again but you are going to go *find* her. this is what
  #    she looks like. a directory is created that has a large number of
  #    subdirectories that have files in them named after different animals,
  #    and one of them has the picture of your kitty. the user is told they
  #    need to find their kitty and move her to their house.txt. The unlock
  #    script compares the contents of house.txt to the picture of the kitty
  # #. the user is told to define specific environment variables that spell
  #    something fun, MADLIBS!
  # #. A short paragraph has had random words replaced with fruits. This
  #    passage is not about fruits. The user must replace all the fruits with
  #    correct words deduced from context using sed.

if __name__ == '__main__' :

  code_to_file(main.__code__,'unlock')

  utils.term.bgcolor = 'black'
  with open('moai.txt','wt') as f :
    f.write(image.Image('moai.png'))
