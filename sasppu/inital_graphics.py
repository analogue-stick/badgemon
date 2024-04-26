import sasppu
from socket import *

screen = sasppu.render()

def dump_over_TCP():
    s = socket()
    s.connect(getaddrinfo('0.0.0.0', 1234, 0, SOCK_STREAM)[0][-1])
    s.send(sasppu.render())
    s.close()
