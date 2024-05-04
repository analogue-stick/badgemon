from asyncio import Event
import math
from typing import List, Tuple

class Animation:
    def __init__(self, length: int=1000, infinite=False) -> None:
        assert(length >= 0)
        self._next: List["Animation"] = []
        self._prev: List["Animation"] = []
        self._ends: List["Animation"] = []
        self._ended_by: List["Animation"] = []
        self._length: int = length
        self._needed_to_start: int = 0
        self._needed_to_start_bak: int = 0
        self._needed_to_end: int = 0
        self._needed_to_end_bak: int = 0
        self._started: bool = False
        self._ended: bool = False
        self._infinite: bool = False

    def _update(self, time: float) -> None:
        pass

    def on_anim_start(self) -> None:
        self._started = True

    def on_anim_end(self) -> None:
        self._ended = True

    def reset(self) -> None:
        self._ended = False
        self._started = False
        self._needed_to_start = self._needed_to_start_bak
        self._needed_to_end = self._needed_to_end_bak

    def and_then(self, next: "Animation") -> "Animation":
        self._next.append(next)
        next._prev.append(self)
        next._needed_to_start += 1
        next._needed_to_start_bak = next._needed_to_start
        return next
    
    def but_also(self, next: "Animation", sync: bool=False) -> "Animation":
        next._prev.extend(self._prev)
        for p in self._prev:
            p.next.append(next)
        if sync:
            next._next.extend(self._next)
            for n in self._next:
                n._prev.append(next)
        return next
    
    def after(self, prev: "Animation") -> "Animation":
        prev._next.append(self)
        self._prev.append(prev)
        self._needed_to_start += 1
        self._needed_to_start_bak = self._needed_to_start
        return self

    def start_on_all(self) -> "Animation":
        self._needed_to_start = len(self._prev)
        self._needed_to_start_bak = self._needed_to_start
        return self

    def start_on_any(self) -> "Animation":
        if len(self._prev) > 0:
            self._needed_to_start = 1
        else:
            self._needed_to_start = 0
        self._needed_to_start_bak = self._needed_to_start
        return self
    
    def ends(self, next: "Animation") -> "Animation":
        self._ends.append(next)
        next._ended_by.append(self)
        next._needed_to_end += 1
        next._needed_to_end_bak = next._needed_to_end
        return self
    
    def ended_by(self, next: "Animation") -> "Animation":
        next._ends.append(self)
        self._ended_by.append(next)
        self._needed_to_end += 1
        self._needed_to_end_bak = self._needed_to_end
        return self
    
    def end_on_all(self) -> "Animation":
        self._needed_to_end = len(self._ended_by)
        self._needed_to_end_bak = self._needed_to_end
        return self

    def end_on_any(self) -> "Animation":
        if len(self._ended_by) > 0:
            self._needed_to_end = 1
        else:
            self._needed_to_end = 0
        self._needed_to_end_bak = self._needed_to_end
        return self

class AnimationEvent(Animation):
    def __init__(self, event: Event, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._trigger_event = event

    def on_anim_end(self, *args, **kwargs) -> None:
        self._trigger_event.set()
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
    def _fun(time: float) -> float:
        return time % 1.0

    def __init__(self, other: Animation, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._other = other
        self._infinite = True

    def reset(self) -> None:
        self.other.reset()
        return super().reset()
    
    def on_anim_end(self) -> None:
        self.other.on_anim_end()
        return super().on_anim_end()
    
    def on_anim_start(self) -> None:
        self.other.on_anim_start()
        return super().on_anim_start()
    
    def _update(self, time: float) -> None:
        self.other.update(self._fun(time))
        return super().update(time)
    
class AnimBounce(AnimCycle):
    def _fun(time: float) -> float:
        if time % 2.0 < 1:
            return time % 1.0
        else:
            return 1.0 - (time % 1.0)

class AnimSin(AnimCycle):
    def _fun(time: float) -> float:
        return math.sin(time*math.tau)

class EditorAnim(Animation):
    def _fun(start:float,end:float,time:float):
        return start

    def __init__(self, editor:function, start:float=0, end:float=1, *args, **kwargs) -> None:
        self._start = start
        self._end = end
        self._editor = editor
        super().__init__(*args, **kwargs)

    def update(self, time: float) -> None:
        self._editor(self._fun(self._start,self._end,time))
        return super().update(time)
    
    def on_anim_start(self) -> None:
        self._editor(self._start)
        return super().on_anim_start()

    def on_anim_end(self) -> None:
        self._editor(self._end)
        return super().on_anim_end()

class AnimLerp(EditorAnim):
    _fun = lerp

class AnimSStep(EditorAnim):
    _fun = sstep

class AnimFaster(EditorAnim):
    _fun = faster

class AnimSlower(EditorAnim):
    _fun = slower

class AnimRandom(EditorAnim):
    _fun = scaled_hash_without_sine

class AnimationScheduler:
    def __init__(self) -> None:
        self._active: List[Tuple[int,Animation]] = []
        self._time: int = 0
        self._event_stream: List[Tuple[int, Animation]] = []

    def update(self, delta: int) -> None:
        end_time = self._time + delta
        while True:
            if len(self._event_stream) == 0:
                self._time = end_time
                break
            event = self._event_stream.pop(0)
            self._time = event[0]
            if self._time >= end_time:
                self._event_stream.insert(0, event)
                self._time = end_time
                break
            anim = event[1]
            anim.on_anim_end()
            for next in anim._next:
                next._needed_to_start -= 1
                if next._needed_to_start <= 0 and not next._started:
                    self.trigger(next)
            for ends in anim._ends:
                ends._needed_to_end -= 1
                if ends._needed_to_end <= 0 and not ends._ended:
                    if not ends._started:
                        self.trigger(ends)
                    else:
                        self._end(ends, end=self._time)
        
        self._active[:] = [i for i in self._active if not i[1]._ended]

        for start, anim in self._active:
            local_time = (self._time - start) / anim._length
            anim._update(local_time)

    def trigger(self, anim: Animation) -> None:
        self._active.append((self._time,anim))
        anim.on_anim_start()
        if anim._needed_to_end <= 0:
            self._end(anim, self._time)
        elif not anim._infinite:
            self._end(anim, self._time + anim._length)

    def _end(self, anim: Animation, end: int) -> None:
        index = 0
        while index < len(self._event_stream) and self._event_stream[index][0] < end:
            index += 1
        self._event_stream.insert(index,(end,anim))