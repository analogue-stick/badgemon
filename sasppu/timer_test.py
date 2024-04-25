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
from machine import SPI, Pin

spi = SPI(1, sck=10)
dc = Pin(8, mode=Pin.OUT, value=0)
cs = Pin(9, mode=Pin.OUT, value=0)
rst = Pin(12, mode=Pin.OUT, value=0)
bl = Pin(40, mode=Pin.OUT, value=0)
sasppu.init_display(spi, dc, cs, rst, bl)

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
    return (then_cpu-now_cpu)/160000

