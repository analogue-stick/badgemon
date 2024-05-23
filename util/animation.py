from asyncio import Event
import math
from sys import implementation as _sys_implementation
if _sys_implementation.name != "micropython":
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
        self._update(0)
        self._started = True

    def on_anim_end(self) -> None:
        self._update(1)
        self._ended = True

    def reset(self) -> None:
        self._ended = False
        self._started = False
        self._needed_to_start = self._needed_to_start_bak
        self._needed_to_end = self._needed_to_end_bak

    def and_then(self, next: "Animation") -> "Animation":
        '''
        Triggers "next" when "self" finishes.
        '''
        self._next.append(next)
        next._prev.append(self)
        next._needed_to_start += 1
        next._needed_to_start_bak = next._needed_to_start
        return next
    
    def but_also(self, next: "Animation", sync: bool=False) -> "Animation":
        '''
        Triggers "next" when the animations that trigger "self" finish.
        Essentially run "next" when "self" runs.
        If sync is True the things that "self" triggers will also wait on "next" before starting.
        '''
        next._prev.extend(self._prev)
        for p in self._prev:
            p.next.append(next)
        if sync:
            next._next.extend(self._next)
            for n in self._next:
                n._prev.append(next)
        return next
    
    def after(self, prev: "Animation") -> "Animation":
        """
        Triggers "self" when "next" finishes.
        """
        prev._next.append(self)
        self._prev.append(prev)
        self._needed_to_start += 1
        self._needed_to_start_bak += 1
        return self

    def start_on_all(self) -> "Animation":
        """
        All animations that could start this animation have to finish before it starts.
        """
        self._needed_to_start = len(self._prev)
        self._needed_to_start_bak = self._needed_to_start
        return self

    def start_on_any(self) -> "Animation":
        """
        Any of the animations that could start this animation will trigger it.
        """
        if len(self._prev) > 0:
            self._needed_to_start = 1
        else:
            self._needed_to_start = 0
        self._needed_to_start_bak = self._needed_to_start
        return self
    
    def ends(self, next: "Animation") -> "Animation":
        """
        When "self" ends, "next" will also end.
        """
        self._ends.append(next)
        next._ended_by.append(self)
        next._needed_to_end += 1
        next._needed_to_end_bak += 1
        return self
    
    def ended_by(self, next: "Animation") -> "Animation":
        """
        When "next" ends, "self" will also end.
        """
        next._ends.append(self)
        self._ended_by.append(next)
        self._needed_to_end += 1
        self._needed_to_end_bak += 1
        return self
    
    def end_on_all(self) -> "Animation":
        """
        All animations that could end this animation have to finish before it ends.
        """
        self._needed_to_end = len(self._ended_by)
        self._needed_to_end_bak = self._needed_to_end
        return self

    def end_on_any(self) -> "Animation":
        """
        Any of the animations that could end this animation will end it.
        """
        if len(self._ended_by) > 0:
            self._needed_to_end = 1
        else:
            self._needed_to_end = 0
        self._needed_to_end_bak = self._needed_to_end
        return self
    
    def clear_ends(self):
        '''
        This animation will end no other animations.
        '''
        for anim in self._ends:
            anim._ended_by.remove(self)
            anim._needed_to_end -= 1
            anim._needed_to_end_bak -= 1
        self._ends.clear()

    def clear_triggers(self):
        '''
        This animation will start no other animations.
        '''
        for anim in self._next:
            anim._prev.remove(self)
        self._next.clear()

    def clear_ended_by(self):
        '''
        This animation will by ended by no other animations.
        '''
        for anim in self._ended_by:
            anim._ends.remove(self)
        self._ended_by.clear()

    def clear_triggered_by(self):
        '''
        This animation will by started by no other animations.
        '''
        for anim in self._prev:
            anim._next.remove(self)
        self._prev.clear()

    def detach(self):
        '''
        This animation is removed from the animation flow.
        Runs all 4 clear commands.
        '''
        self.clear_ended_by()
        self.clear_ends()
        self.clear_triggered_by()
        self.clear_triggers()

class AnimationEvent(Animation):
    '''
    Animation that does nothing, but sets a given event when it finishes.
    Used to wait until animations finish in normal code. Will clear the event on reset.
    '''
    def __init__(self, event: Event, length: int = 0, *args, **kwargs) -> None:
        super().__init__(length, *args, **kwargs)
        self._trigger_event = event

    def on_anim_end(self, *args, **kwargs) -> None:
        self._trigger_event.set()
        return super().on_anim_end(*args, **kwargs)
    
    def reset(self) -> None:
        self._trigger_event.clear()
        return super().reset()

class AnimationWait(Animation):
    '''
    Does absolutely nothing. Used to put pauses in animations, e.g. "x" and_then "wait (1000ms)" and_then "y"
    '''
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
    '''
    Repeats the given animation forever, with a saw-wave like pattern
    '''
    def _fun(self, time: float) -> float:
        return time % 1.0

    def __init__(self, other: Animation, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._other = other
        self._infinite = True

    def reset(self) -> None:
        self._other.reset()
        return super().reset()
    
    def on_anim_end(self) -> None:
        self._other.on_anim_end()
        return super().on_anim_end()
    
    def on_anim_start(self) -> None:
        self._other.on_anim_start()
        return super().on_anim_start()
    
    def _update(self, time: float) -> None:
        self._other._update(self._fun(time))
        return super()._update(time)
    
class AnimBounce(AnimCycle):
    '''
    Repeats the given animation forever, with a triangle-wave like pattern
    '''
    def _fun(self, time: float) -> float:
        if time % 2.0 < 1:
            return time % 1.0
        else:
            return 1.0 - (time % 1.0)

class AnimSin(AnimCycle):
    '''
    Repeats the given animation forever, with a sine-wave like pattern
    '''
    def _fun(self, time: float) -> float:
        return math.sin(time*math.tau)

class EditorAnim(Animation):
    '''
    Calls a function with the result of a curve between start and end.
    '''
    def _fun(self, start:float,end:float,time:float):
        return start

    def __init__(self, editor:callable, start:float=0, end:float=1, *args, **kwargs) -> None:
        self._start = start
        self._end = end
        self._editor = editor
        super().__init__(*args, **kwargs)

    def _update(self, time: float) -> None:
        self._editor(self._fun(self._start,self._end,time))
        return super()._update(time)
    
    def on_anim_start(self) -> None:
        self._editor(self._start)
        return super().on_anim_start()

    def on_anim_end(self) -> None:
        self._editor(self._end)
        return super().on_anim_end()

class AnimLerp(EditorAnim):
    '''
    Calls the editor function with a linear function.
    '''
    def _fun(self, start: float, end: float, time: float):
        return lerp(start, end, time)

class AnimSStep(EditorAnim):
    '''
    Calls the editor function with a smoothstep function.
    '''
    def _fun(self, start: float, end: float, time: float):
        return sstep(start, end, time)

class AnimFaster(EditorAnim):
    '''
    Calls the editor function with an Ease In function.
    '''
    def _fun(self, start: float, end: float, time: float):
        return faster(start, end, time)

class AnimSlower(EditorAnim):
    '''
    Calls the editor function with an Ease Out function.
    '''
    def _fun(self, start: float, end: float, time: float):
        return slower(start, end, time)

class AnimRandom(EditorAnim):
    '''
    Calls the editor function with randomish values. They are deterministic.
    '''
    def _fun(self, start: float, end: float, time: float):
        return scaled_hash_without_sine(start, end, time)

class AnimationScheduler:
    def __init__(self) -> None:
        self._active: List[Tuple[int,Animation]] = []
        self._time: int = 0
        self._event_stream: List[Tuple[int, Animation]] = []

    def update(self, delta: int) -> None:
        '''
        Updates all animations.
        This works by keeping track of the global time in milliseconds, and then works out how far
        through each animation is and calls the update function with this float.
        Before this it will run through the eventstram for this frame, which contains all the end times
        for the animations. If the animation ends this frame it will end, any animations that come after it
        will be started, and any animations that are ended by that animations are scheduled for ending next.
        '''
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
        '''
        Starts an animation. The animation will be updated every frame if the app is foregrounded.
        If the animation is not infinite the end of the animation will be scheduled.
        '''
        self._active.append((self._time,anim))
        anim.on_anim_start()
        if anim._needed_to_end <= 0 and len(anim._ended_by) > 0:
            self._end(anim, self._time)
        elif not anim._infinite:
            self._end(anim, self._time + anim._length)

    def _end(self, anim: Animation, end: int) -> None:
        '''
        Ends an animation. This is accomplished by inserting an event into the eventstream
        at the relevant position in time. This is therefore called on trigger of an animation
        if the animation has a fixed end point. To end an animation as soon as possible, set
        end to the current time.
        '''
        index = 0
        while index < len(self._event_stream) and self._event_stream[index][0] < end:
            index += 1
        self._event_stream.insert(index,(end,anim))

    def kill_animation(self) -> None:
        '''
        Stops all animations immediately.
        Calls the on anim end then resets the entire class by calling __init__
        This means that all the relevant lists are cleared, but also sets time to 0,
        because time will simply go on forever if not.
        '''
        for anim in self._active:
            anim[1].on_anim_end()
        self.__init__()