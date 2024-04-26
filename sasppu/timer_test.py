import time
def timer():
    now = time.ticks_us()
    now_cpu = time.ticks_cpu()
    for i in range(100):
        print("IGNORE")
    then = time.ticks_us()
    then_cpu = time.ticks_cpu()
    print(then-now)
    print(then_cpu-now_cpu)
    print((then_cpu-now_cpu)/(then-now))

import sasppu
import gc9a01py
from machine import SPI, Pin

spi = SPI(1, baudrate=80000000, sck=10)
dc = Pin(8, mode=Pin.OUT, value=0)
cs = Pin(9, mode=Pin.OUT, value=0)
rst = Pin(12, mode=Pin.OUT, value=0)
bl = Pin(40, mode=Pin.OUT, value=0)
thing = gc9a01py.GC9A01(spi,dc,cs,rst,bl)
rd= sasppu.render()
thing.blit_buffer(rd, 0,0,240,240)

def timer_sasppu():
    now_cpu = time.ticks_cpu()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    sasppu.render()
    then_cpu = time.ticks_cpu()
    return (time.ticks_diff(then_cpu,now_cpu))/160000

