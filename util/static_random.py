import math

import time

# Dave Hoskins
def hash_without_sine(p:float):
    p *= .1031
    p = p - math.trunc(p)
    p *= p + 33.33
    p *= p + p
    return p - math.trunc(p)

state = 0

def new_state():
    global state
    state = int(random()*(2**24))

def set_state(s):
    global state
    state = int(s) % (2**24)

set_state(time.time())

def random():
    global state
    r = hash_without_sine(state)
    state = (state + 1) % (2**24)
    return r

def getrandbits(n):
    return int(random()*(2**n))

def randrange(start, end):
    return int((random()*(end-start))+start)

def randint(start, end):
    return randrange(start, end)

def choice(choices):
    return choices[int(random()*len(choices))]