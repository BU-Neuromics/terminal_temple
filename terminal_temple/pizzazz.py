from itertools import product, cycle
from fabulous import text
from fabulous.color import *
from fabulous.utils import TerminalInfo
import random
import sys
import termios
import tty
from time import sleep

flags = termios.tcgetattr(sys.stdout)

term = TerminalInfo()

def set_echo_and_icanon(flag) :
    if flag :
        new = flags.copy()
        new[3] = new[3] | termios.ECHO | termios.ICANON
    else :
        new = flags.copy()
        new[3] = new[3] & ~termios.ECHO & ~termios.ICANON
    termios.tcsetattr(sys.stdout, termios.TCSANOW, new)
    pass

def write(o) :
    sys.stdout.write(str(o))
    sys.stdout.flush()

def move(x,y) :
    write('\033[{};{}H'.format(y,x))

def up(n) :
    write('\033[{}A'.format(n))

hex_chars = '0123456789ABCDEF'
def random_color() :
    return '#{}'.format(''.join(random.choices(hex_chars,k=6)))

def rect(x1,y1,x2,y2,color) :

    term = TerminalInfo()

    positions = list(
            product(
                range(max(0,x1),min(x2,term.width)),
                range(max(0,y1),min(y2,term.height))
            )
    )
    for x,y in positions :
        move(x,y)
        write(bg256(color,' '))

def type_text(text,speed=0.03) :
    variance = 1
    for c in str(text) :
        write(c)
        jitter_speed = speed*((1-variance/2)+random.random()*variance)**2
        sleep(jitter_speed)

def type_texts(texts,speed=0.03,delay=1):
    for text in texts :
        sleep(delay)
        type_text(text,speed=speed)
        if texts.index(text) != len(texts)-1 :
            write(' ')
    sleep(delay)

banner_color = '#786d5f'
def banner() :

    term = TerminalInfo()

    voffset = 4
    rect(0,int(term.height/voffset-2),term.width,int(term.height/voffset+26),'#000')
    move(0,int(term.height/voffset))
    write(text.Text(' terminal',skew=5,shadow=True,color=banner_color))
    move(0,int(term.height/voffset+12))
    write(text.Text('  temple',skew=5,shadow=True,color=banner_color))

def dazzle() :

    term = TerminalInfo()

    positions = list(product(range(term.width),range(term.height)))
    random.shuffle(positions)
    for x,y in positions :
        move(x,y)
        write(bg256(random_color(),' '))
        sleep(0.0001)

def clear() :
    write('\033[2J')

if __name__ == '__main__' :

    clear()

    move(0,0)
    type_text(green("Thanks for playing"))
    sleep(1)
    type_text(green("\nThat was fun"))
    sleep(1)

    set_echo_and_icanon(0)
    try :
        dazzle()
    finally :
        set_echo_and_icanon(1)
        banner()
        sleep(5)
        move(0,term.height)
