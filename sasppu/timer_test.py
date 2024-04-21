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