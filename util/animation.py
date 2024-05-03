from asyncio import Event
import math
from typing import List, Tuple

class Animation:
    def __init__(self, length: int=1000, infinite=False) -> None:
        assert(length >= 0)
        self.next: List["Animation"] = []
        self.prev: List["Animation"] = []
        self.ends: List["Animation"] = []
        self.length: int = length
        self.needed_to_start: int = 0
        self.needed_to_start_bak: int = 0
        self.started: bool = False
        self.ended: bool = False
        self.infinite: bool = False

    def update(self, time: float) -> None:
        pass

    def on_anim_start(self) -> None:
        self.started = True

    def on_anim_end(self) -> None:
        self.ended = True

    def reset(self) -> None:
        self.ended = False
        self.started = False
        self.needed_to_start = self.needed_to_start_bak

    def and_then(self, next: "Animation") -> "Animation":
        self.next.append(next)
        next.prev.append(self)
        next.needed_to_start += 1
        next.needed_to_start_bak = next.needed_to_start
        return next
    
    def but_also(self, next: "Animation", sync: bool=False) -> "Animation":
        next.prev.extend(self.prev)
        for p in self.prev:
            p.next.append(next)
        if sync:
            next.next.extend(self.next)
            for n in self.next:
                n.prev.append(next)
        return next
    
    def after(self, prev: "Animation") -> "Animation":
        prev.next.append(self)
        self.prev.append(prev)
        self.needed_to_start += 1
        self.needed_to_start_bak = self.needed_to_start
        return self

    def wait_on_all(self) -> "Animation":
        self.needed_to_start = len(self.prev)
        self.needed_to_start_bak = self.needed_to_start
        return self

    def wait_on_any(self) -> "Animation":
        if len(self.prev) > 0:
            self.needed_to_start = 1
        else:
            self.needed_to_start = 0
        self.needed_to_start_bak = self.needed_to_start
        return self
    
    def ends(self, next: "Animation") -> "Animation":
        self.ends.append(next)
        return self
    
    def ended_by(self, next: "Animation") -> "Animation":
        next.ends.append(self)
        return self

class AnimationEvent(Animation):
    def __init__(self, event: Event, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.trigger_event = event

    def on_anim_end(self, *args, **kwargs) -> None:
        self.trigger_event.set()
        return super().on_anim_end(*args, **kwargs)

class AnimationWait(Animation):
    pass

def lerp(start:float=0, end:float=1, time:float=0):
    return (end*time) + (start*(1-time))

def sstep(start:float=0, end:float=1, x:float=0):
    return lerp(start, end, x * x * (3.0 - 2.0 * x))

def faster(start:float=0, end:float=1, x:float=0):
    return lerp(start, end, x * x * 0.5 * (3.0 - x))

def slower(start:float=0, end:float=1, x:float=0):
    x += 1
    return lerp(start, end, (x * x * 0.5 * (3.0 - x)) - 1)

# Dave Hoskins
def hash_without_sine(p:float):
    p *= .1031
    p = p - math.trunc(p)
    p *= p + 33.33
    p *= p + p
    return p - math.trunc(p)

def scaled_hash_without_sine(start,end,p):
    return lerp(start,end,hash_without_sine(lerp(start,end*100,p)))

class AnimCycle(Animation):
    def fun(time: float) -> float:
        return time % 1.0

    def __init__(self, other: Animation, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.other = other
        self.infinite = True

    def reset(self) -> None:
        self.other.reset()
        return super().reset()
    
    def on_anim_end(self) -> None:
        self.other.on_anim_end()
        return super().on_anim_end()
    
    def on_anim_start(self) -> None:
        self.other.on_anim_start()
        return super().on_anim_start()
    
    def update(self, time: float) -> None:
        self.other.update(self.fun(time))
        return super().update(time)
    
class AnimBounce(AnimCycle):
    def fun(time: float) -> float:
        if time % 2.0 < 1:
            return time % 1.0
        else:
            return 1.0 - (time % 1.0)

class AnimSin(AnimCycle):
    def fun(time: float) -> float:
        return math.sin(time*math.tau)

class EditorAnim(Animation):
    def fun(start:float,end:float,time:float):
        return start

    def __init__(self, editor:function, start:float=0, end:float=1, *args, **kwargs) -> None:
        self.start = start
        self.end = end
        self.editor = editor
        super().__init__(*args, **kwargs)

    def update(self, time: float) -> None:
        self.editor(self.fun(self.start,self.end,time))

class AnimLerp(EditorAnim):
    fun = lerp

class AnimSStep(EditorAnim):
    fun = sstep

class AnimFaster(EditorAnim):
    fun = faster

class AnimSlower(EditorAnim):
    fun = slower

class AnimRandom(EditorAnim):
    fun = scaled_hash_without_sine

class AnimationCoordinator:
    def __init__(self) -> None:
        self.active: List[Tuple[int,Animation]] = []
        self.time: int = 0

    def update(self, delta: int):
        self.time += delta
        for start, anim in self.active:
            local_time = (self.time - start) / anim.length
            if not anim.infinite and local_time > 1:
                self.end(anim)
            else:
                anim.update(local_time)

        self.active[:] = [i for i in self.active if not i[1].ended]

    def trigger(self, anim: Animation):
        self.active.append((self.time,anim))
        anim.on_anim_start()

    def end(self, anim: Animation):
        anim.on_anim_end()
        for next in anim.next:
            next.needed_to_start -= 1
            if next.needed_to_start <= 0 and not next.started:
                self.trigger(next)
        for ends in anim.ends:
            if ends.started and not ends.ended:
                self.end(ends)
