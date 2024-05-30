from asyncio import Event
import asyncio
from ctx import Context
from ..game.mons import Mon
from ..util.animation import AnimFaster, AnimLerp, AnimRandom, AnimationEvent, AnimationWait

from ..scenes.scene import Scene
from ..util.misc import draw_mon

class LevelUp(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mon = None
        self.mon_index = 0
        for i,m in enumerate(self.context.player.badgemon):
            if m.level_up_needed():
                self.mon = m
                self.mon_index = i
                break
        self.replace_chosen = False
        self.mon_x = 0
        self.mon_y = 0
        self.scale = 1

    def redirect(self):
        if self.mon is None:
            return 2
        return None

    def _replace_move(self, mon, index, move):
        def f():
            mon.moves[index] = move
            self.replace_chosen = True
        return f
    
    def _set_mon_x(self, x):
        self.mon_x = x

    def _set_mon_y(self, y):
        self.mon_y = y

    def _set_scale(self, s):
        self.scale = s

    def draw(self, ctx: Context):
        super().draw(ctx)
        draw_mon(ctx, self.mon.template.sprite, -64+self.mon_x*self.scale, -64+self.mon_y*self.scale, False, False, 4)

    async def background_task(self):
        await self.speech.write(f"{self.mon.nickname} leveled up!")
        self.mon.level += 1
        await self.speech.write(f"{self.mon.nickname} is now level {self.mon.level}")
        for move, lvl in self.mon.template.learnset:
            if lvl == self.mon.level:
                if len(self.mon.moves) < 4:
                    self.mon.moves.append(move)
                    await self.speech.write(f"{self.mon.nickname} learnt {move.name}!")
                else:
                    await self.speech.write(f"{self.mon.nickname} would like to learn {move.name}. Please select a move to replace, or press back to abandon learning the move.")
                    self.replace_chosen = False
                    self.choice.set_choices(
                        (
                            move.name,
                                [(move.name, self._replace_move(self.mon, index, move)) for index, move in enumerate(self.mon.moves)]
                        )
                    )
                    self.choice.open()
                    await self.choice.closed_event.wait()
                    if self.replace_chosen:
                        await self.speech.write(f"{self.mon.nickname} learnt {move.name}!")
                    else:
                        await self.speech.write(f"{self.mon.nickname} did not learn {move.name}.")
        self.mon.calculate_stats()
        await self.speech.write(f"{self.mon.nickname}'s stats updated!")
        if self.mon.template.evolve_level and self.mon.template.evolve_mon:
            if self.mon.template.evolve_level == self.mon.level:
                await asyncio.sleep(1)
                await self.speech.write(f"Wait, what's happening???")
                rndx = AnimRandom(editor=lambda x: self._set_mon_x(x), start=-1, length=2837, infinite=True)
                rndy = AnimRandom(editor=lambda y: self._set_mon_y(y), start=-1, length=4526, infinite=True)
                scaleanim = AnimFaster(editor=lambda s: self._set_scale(s*30), length=5000)
                self._fader.detach()
                self._fader.ends(rndx)
                self._fader.ends(rndy)
                self._fader.ends(scaleanim)
                self._fader._colour = (1,1,1)
                self._fader.reset(fadein=False)
                self._fader._length = 5000
                endevent = Event()
                animend = AnimationEvent(endevent)
                self._fader.and_then(animend)
                starter = AnimationWait(length=0)
                starter.and_then(rndx).but_also(rndy).but_also(scaleanim).but_also(self._fader)
                self.animation_scheduler.trigger(starter)
                await endevent.wait()
                new_mon = Mon(self.mon.template.evolve_mon, self.mon.level, self.mon.ivs, self.mon.evs, self.mon.moves)
                new_mon.set_nickname(self.mon.nickname)
                new_mon.xp = self.mon.xp
                self.context.player.badgemon[self.mon_index] = new_mon
                self.mon = new_mon
                self._fader.reset(fadein=True)
                self._fader._length = 1000
                animend.reset()
                self.mon_x = 0
                self.mon_y = 0
                self.scale = 0
                self.animation_scheduler.trigger(self._fader)
                await endevent.wait()
                self._fader._length = 200
                await asyncio.sleep(2)
                await self.speech.write(f"{self.mon.nickname} evolved into {self.mon.template.name}!")
                self.context.player.badgedex.find(self.mon.template.id)
                self.mon.calculate_stats()
                await self.speech.write(f"{self.mon.nickname}'s stats updated!")

        await self.fade_to_scene(7)