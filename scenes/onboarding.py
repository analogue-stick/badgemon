from asyncio import Event
import asyncio
from ..util import static_random as random

from ctx import Context

from ..game.mons import Mon, mons_list

from ..config import ASSET_PATH

from ..util.animation import AnimationEvent
from ..util.misc import *

from ..scenes.scene import Scene
class Onboarding(Scene):
    def _set_wobble(self, x):
        self._arrow_wobble = x

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fade_complete = Event()
        self._slide = None
        self._bmons = []
        for _ in range(3):
            self._bmons.append(Mon(random.choice(mons_list), 5))
        self._picked_mon = None

    async def _switch_to(self, slide):
        self._end_event.reset()
        self._fader.reset(fadein=False)
        self.animation_scheduler.trigger(self._fader)
        await self._fade_complete.wait()
        self._slide = slide
        self._end_event.reset()
        self._fader.reset(fadein=True)
        self.animation_scheduler.trigger(self._fader)
        await self._fade_complete.wait()
        await asyncio.sleep(0.5)

    def draw(self, ctx: Context):
        super().draw(ctx)
        ctx.image_smoothing = 0
        if self._slide is not None:
            if self._slide == "BMONSLIDE":
                for m in range(3):
                    draw_mon(ctx, self._bmons[m].template.sprite, 80*(m-1)-(16*2), -(16*2), False, False, 2)
            else:
                ctx.image(self._slide,-120,-120,240,240)

    def _mon_pick(self, mon: Mon):
        def f():
            self._picked_mon = mon
        return f

    async def background_task(self):
        self._fader.detach()
        self._end_event = AnimationEvent(self._fade_complete)
        self._fader.and_then(self._end_event)
        self._fader._colour = (0.9,0.9,0.9)
        self._fader.reset(fadein=False)
        await asyncio.sleep(0.5)
        await self._switch_to(ASSET_PATH+"onboard/arm.png")
        await self.speech.write("Hello there! Welcome to the world of BADGEMON! My name is Acorn R. Machine. People call me the BADGEMON PROF!")
        await self._switch_to(ASSET_PATH+"mons/mon-1.png")
        await self.speech.write("This field in the middle of England is inhabited by creatures called BADGEMON! For some people, BADGEMON are pets. Others consider them \'a nuisance\' and \'not covered by the insurance\'. Myself... I study BADGEMON as a profession.")
        await self._switch_to(ASSET_PATH+"onboard/you.png")
        await self.speech.write("First, what is your name?")
        player_name = await self.text.wait_for_answer("Your name?", "SCARLETT")
        self.context.player.name = player_name
        await self.speech.write(f"Right! So your name is {player_name}!")
        await self._switch_to(ASSET_PATH+"onboard/son.png")
        await self.speech.write("This is my grandson. He's unrelated to the BADGEMON, I just wanted to show you his picture. Isn't he the best? I'm very proud of him.")
        await self._switch_to(None)
        await self.speech.write("Soon you will be able explore the world of BADGEMON! First though, we have one more task to complete. You need a badgemon yourself!")
        await self._switch_to("BMONSLIDE")
        await self.speech.write("Here are three badgemon that I don't want anymore, and I'm pawning them off on you.")
        await self.speech.write(f"On the left is {self._bmons[0].template.name}. They are described as: {self._bmons[0].template.desc}")
        await self.speech.write(f"In the middle is {self._bmons[1].template.name}. They are described as: {self._bmons[1].template.desc}")
        await self.speech.write(f"On the right is {self._bmons[2].template.name}. They are described as: {self._bmons[2].template.desc}")
        await self.speech.write("So? Who do you want?")
        self.choice.set_choices(("Pick a mon!", [(m.template.name, self._mon_pick(m)) for m in self._bmons]), True)
        await asyncio.sleep(0.1)
        await self.choice.closed_event.wait()
        await self._switch_to(ASSET_PATH+f"mons/mon-{self._picked_mon.template.sprite}.png")
        await self.speech.write(f"Ah, so you picked {self._picked_mon.nickname}! I'll send these other two to... a farm up north.")
        await self.speech.write("What will you name your badgemon? Enter nothing for a default.")
        self._picked_mon.nickname = await self.text.wait_for_answer("Nickname?", self._picked_mon.nickname.upper())
        self.context.player.badgemon.append(self._picked_mon)
        self.context.player.badgedex.find(self._picked_mon.template.id)
        await self.speech.write(f"{self._picked_mon.nickname} has been added to your badgemon party!")
        await self._switch_to(ASSET_PATH+"onboard/you.png")
        await self.speech.write(f"{player_name}! Your very own BADGEMON legend is about to unfold! A whole field of dreams and adventures and tents and seminars with BADGEMON awaits! Let's go!")
        await self._switch_to(None)
        await self.fade_to_scene(4)