from asyncio import Event
import asyncio
from ..util import static_random as random
from sys import implementation as _sys_implementation
if _sys_implementation.name != "micropython":
    from typing import Coroutine

from ..game.player import Cpu, Player

from ..scenes.scene import Scene
from ..game.items import Item, items_list
from ..game.mons import Mon, mons_list, choose_weighted_mon
from ..util.misc import shrink_until_fit, draw_mon
from ..protocol import packet
from events.input import ButtonDownEvent
from ctx import Context
from ..game.customisation import COLOURS, PATTERNS

potion = items_list[0]
mon_template1 = mons_list[0]
mon_template2 = mons_list[1]
mon1 = Mon(mon_template1, 5).set_nickname("small guy")
mon2 = Mon(mon_template2, 17).set_nickname("mr. 17")
mon3 = Mon(mon_template1, 17).set_nickname("David")
mon4 = Mon(mon_template2, 33).set_nickname("large individual")
mon5 = Mon(mon_template1, 100).set_nickname("biggest dude")

class Field(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._next_move_available = Event()
        self._next_move = None
        self._fight_accept_available = Event()
        self._fight_accept = None
        self._device_available = Event()
        self._device = None
        self._advertise_reset = Event()
        self._exit = False
        self._random_enc_needed = Event()
        self._tasks_finished = Event()
        self.adv = None
        if len(self.context.player.badgemon) == 0:
            self.context.player.badgemon.append(Mon(mon_template1, 5).set_nickname("LIL GUY"))
        try:
            self._gen_field_dialog()
        except Exception as e:
            print(e)
        self.sm._attempt_save()

    def redirect(self):
        for m in self.context.player.badgemon:
            if m.level_up_needed():
                return 7

    def _get_answer(self, ans: Coroutine, exit = False):
        return lambda: self._get_answer_internal(ans,exit)

    def _get_answer_internal(self, ans: Coroutine, exit = False):
        self._next_move = ans
        self._exit = exit
        self._next_move_available.set()

    async def _use_item(self, item: Item, count: int, mon: Mon):
        if item.name != "Fishing Rod":
            count -= 1
            if count == 0:
                self.context.player.inventory.pop(item)
            else:
                self.context.player.inventory[item] = count
        await self.speech.write(f"Using {item.name}!")
        if item.name == "Fishing Rod":
            await self.speech.write(f"But wait - You don't have an Eastnor Fishing licence! Try again later.")
            
        item.function_in_field(self.context.player, mon)

    async def _deposit_mon(self, mon: Mon):
        self.context.player.badgemon.remove(mon)
        self.context.player.badgemon_case.append(mon)
        await self.speech.write(f"{mon.nickname} has left your party!")

    async def _move_in_mon(self, mon: Mon):
        self.context.player.badgemon_case.remove(mon)
        self.context.player.badgemon.append(mon)
        await self.speech.write(f"{mon.nickname} has joined your party!")

    async def _swap_mon(self, mon1_index: int, mon2_index: int):
        bm = self.context.player.badgemon
        bm[mon1_index], bm[mon2_index] = bm[mon2_index], bm[mon1_index]
        await self.speech.write(f"{bm[mon1_index].nickname} swapped with {bm[mon2_index].nickname}!")

    async def _describe_item(self, item: Item):
        await self.speech.write(item.desc)

    async def _use_full_heal(self):
        await self.context.player.use_full_heal(self.speech)

    async def _initiate_battle(self):
        template = choose_weighted_mon()
        max_level = max([m.level for m in self.context.player.badgemon])
        level = random.randrange(max(max_level//8,5), int(max_level*1.2))

        await self.fade_to_scene(3, opponent=Cpu(template.name, [Mon(template, level)], [], []))

    async def _save(self):
        self.sm._attempt_save()
        await self.speech.write("Game Saved!")

    async def _purchase(self, item: Item, count: int):
        current = self.context.player.inventory.get(item)
        if current is None:
            current = 0
        self.context.player.inventory[item] = count+current
        self.context.player.money -= item.value*count
        await self.speech.write(f"Bought {count}x {item.name}! Have a nice day!")

    async def _toggle_randomenc(self):
        self.context.random_encounters ^= True
        if self.context.random_encounters:
            await self.speech.write("Random encounters are enabled.")
        else:
            await self.speech.write("Random encounters are disabled.")

    async def _inspect(self, mon: Mon):
        await self.fade_to_scene(8, mon=mon)

    def _set_device(self, dev):
        def f():
            self._device = dev
            self._device_available.set()
        return f

    async def _host_fight(self):
        await self.speech.write("Searching for trainers...", stay_open=True)
        trainers = await self.sm._bt.find_trainers()
        self.speech.close()
        if len(trainers) == 0:
            await self.speech.write("No trainers found.")
        else:
            self.choice.set_choices(("Trainers", [("Cancel", self._set_device(None))] + [(f"{name}", self._set_device(device)) for name, device in trainers]), True)
            self.choice.open()
            await self.choice.opened_event.wait()
            await self.choice.closed_event.wait()
            if self._device_available.is_set():
                self._device_available.clear()
                self.sm.connection_task = asyncio.create_task(self.sm._bt.connect_peripheral(self._device))
                await self.speech.write("Connecting...", stay_open=True)
                try:
                    await asyncio.wait_for(self.sm._bt.connection.wait(), 10)
                except asyncio.TimeoutError:
                    pass
                self.speech.close()
                if not self.sm._bt.connection.is_set():
                    await self.speech.write("Connection failed.")
                else:
                    await self.speech.write("Waiting for user...", stay_open=True)
                    connect = await self.sm._bt._input.get()
                    self.speech.close()
                    if connect[0] == 'N':
                        await self.speech.write("User denied request.")
                    else:
                        await self.sm._bt._output.put(packet.challenge_req_packet(
                            self.context.player, 
                            random.getrandbits(32)
                            ))
                        responsedata = await self.sm._bt._input.get()
                        player = packet.decode_packet(responsedata)
                        assert isinstance(player, Player)
            else:
                print('NUH UH')
                        
    async def _host_fight_dummy(self):
        await self.speech.write("Hello! Molive here. It is extremely likely that I will recieve" +
                                " the badges at the exact same time you will, and therefore will have absolutely no way" +
                                " to test or develop bluetooth functionality beforehand. I will try and add this feature during" +
                                " the event, but don't count on it. Sorry.")
    
    async def _set_bg_col(self, col):
        self.context.custom.background_col = col

    async def _set_fg_col(self, col):
        self.context.custom.foreground_col = col
    
    async def _set_pattern(self, pat):
        self.context.custom.pattern = pat

    def _gen_field_dialog(self):
        if len(self.context.player.badgemon) == 1:
            swap_mon_out = self._get_answer(self.speech.write("You must have at least one badgemon at all times!"))
        else:
            swap_mon_out = ("Deposit BM", [(m.nickname, self._get_answer(self._deposit_mon(m)))for m in self.context.player.badgemon])

        if len(self.context.player.badgemon) == 6:
            swap_mon_in = self._get_answer(self.speech.write("You can have maximum six badgemon!"))
        elif len(self.context.player.badgemon_case) == 0:
            swap_mon_in = self._get_answer(self.speech.write("You have no badgemons in storage!"))
        else:
            swap_mon_in  = ("Withdraw BM ", [(m.nickname, self._get_answer(self._move_in_mon(m))) for m in self.context.player.badgemon_case])

        # this is so cursed
        if len(self.context.player.badgemon) == 1:
            swap_mons = self._get_answer(self.speech.write("You only have one badgemon!"))
        else:
            swap_mons  = ("Pick first mon", [(m1.nickname,
                        (f"Pick Second mon", [(m2.nickname,
                               self._get_answer(self._swap_mon(i, j)), 
                            ) for j, m2 in enumerate(self.context.player.badgemon)])
                        ) for i, m1 in enumerate(self.context.player.badgemon)])
            
        inspect = ("Inspect BMon", [(f"{m.nickname}", self._get_answer(self._inspect(m), True)) for m in self.context.player.badgemon])
            
        usable_items = [(i, c) for (i, c) in self.context.player.inventory.items() if i.usable_in_field and c > 0]

        if len(usable_items) == 0:
            use_item = self._get_answer(self.speech.write("You have no (usable) items!"))
        else:
            use_item = ("Pick an item", [(f"{c}x {i.name}",
                        ("Pick a mon", [(m.nickname,
                                self._get_answer(self._use_item(i, c, m))
                            ) for m in self.context.player.badgemon])
                        ) for (i, c) in usable_items])


        describe_item = ("Descriptions", [(i.name,
                            self._get_answer(self._describe_item(i))
                            ) for i in items_list])
        

        max_purchase = []
        no_purchase = True
        for item in items_list:
            current = self.context.player.inventory.get(item)
            if current is None:
                current = 0
            m = min(self.context.player.money//item.value, 255-current, 10)
            no_purchase &= m == 0
            max_purchase.append((item, m))
            
        if no_purchase:
            shop = self._get_answer(self.speech.write("You don't have enough money!"))
        else:
            shop = (f"GP: {self.context.player.money}", [(f"{item.name}",
                    (f"Cost: {item.value}", [(f"{i}x {item.name}",
                            (f"Buy {i}x {item.name}", [("Confirm",
                                self._get_answer(self._purchase(item,i))
                            )])
                        ) for i in range(1,count+1)])
                    ) for (item, count) in max_purchase if count > 0])
            
        change_bg_col = ("Background Colour", [(col, self._get_answer(self._set_bg_col(col))) for col in COLOURS.keys()])
        change_fg_col = ("Foreground Colour", [(col, self._get_answer(self._set_fg_col(col))) for col in COLOURS.keys()])
        change_pattern = ("Pattern", [(pat, self._get_answer(self._set_pattern(pat))) for pat in PATTERNS])

        options = [
            ("Badgemon", ("Badgemon",[
                ("Heal", self._get_answer(self._use_full_heal())),
                ("Deposit", swap_mon_out),
                ("Withdraw", swap_mon_in),
                ("Order", swap_mons),
                ("Inspect", inspect)
            ])),
            ("Badgedex", self._get_answer(self.fade_to_scene(5), True)),
            ("Item Bag", ("Item Bag", [
                ("Use Item", use_item),
                ("Describe", describe_item),
                ("Buy Item", shop)
            ])),
            ("Customisation", ("Customisation", [
                ("Background", change_bg_col),
                ("Foreground", change_fg_col),
                #("pattern", change_pattern),
            ])),
            #("Host Fight",self._get_answer(self._host_fight())),
            #("Instructions", self._get_answer(self.fade_to_scene(4), True)),
            ("Settings", ("Settings",[
                ("Tog. RandEnc", self._get_answer(self._toggle_randomenc()))
            ])),
            ("Main Menu", ("Main Menu?",[
                ("Confirm", self._get_answer(self.fade_to_scene(0), True))
            ])),
            ("Save", self._get_answer(self._save())),
        ]
        
        if self.context.player.name == "MOLIVE" or self.context.player.name == "NYAALEX":
            options.append(("DEBUG BATTLE", self._get_answer(self._initiate_battle(), True)))

        self.choice.set_choices(
            ("Field", options)
        )

    def draw(self, ctx: Context):
        ctx.rectangle(-120,-120,240,240).rgb(*COLOURS[self.context.custom.background_col]).fill()
        ctx.text_align = Context.LEFT
        ctx.text_baseline = Context.MIDDLE
        ctx.font_size = 25
        ctx.rgb(*COLOURS[self.context.custom.foreground_col])
        ctx.move_to(-105, -35).text("Hi, my name is").fill()
        shrink_until_fit(ctx, self.context.player.name, 220, 60)
        ctx.move_to(-110, 0).text(self.context.player.name).fill()
        ctx.font_size = 20
        ctx.move_to(-105, 35).text(f"Badgedex: {sum(self.context.player.badgedex.found)}/{len(mons_list)}").fill()
        positions = [
            (-34-16, -90 -16),
            (   -16, -100-16),
            ( 34-16, -90 -16),
            (-34-16,  90 -16),
            (  0-16,  100-16),
            ( 34-16,  90 -16),]
        for mon, pos in zip(self.context.player.badgemon, positions):
            draw_mon(ctx, mon.template.sprite, pos[0], pos[1], False, False, 1)
        

    def handle_buttondown(self, event: ButtonDownEvent):
        if not self.choice.is_open() and not self.speech.is_open():
            self._gen_field_dialog()
            self.choice.open()

    async def _await_random_enc(self):
        while True:
            await self._random_enc_needed.wait()
            if not self.context.random_encounters:
                self._random_enc_needed.clear()
            else:
                break
        while self.speech.is_open():
            await self.speech._ready_event.wait()
        self.choice.close()
        await self.speech.write("Oh, what's this?")
        await self._initiate_battle()
        self._tasks_finished.set()  

    def _accept_fight(self, ans: bool):
        def f():
            self._fight_accept = ans
            self._fight_accept_available.set()
        return f

    async def _await_trainer(self):
        while True:
            await self.sm._bt.connection.wait()
            if not self.sm._bt.host:
                while self.speech.is_open():
                    await self.speech._ready_event.wait()
                self.choice.close()
                await self.speech.write(f"{self.sm._bt.conn_name} is looking for a fight! Do you accept?")
                self.choice.set_choices((f"Fight {self.sm._bt.conn_name}", [
                        ("yes", self._accept_fight(True)),
                        ("no", self._accept_fight(False))
                    ]), True)
                self.choice.open()
                await self._fight_accept_available.wait()
                if self._fight_accept:
                    self.sm._bt._output.put("YEAG")
                    pass
                else:
                    self.sm._bt._output.put("NUH-UH")
                    self._advertise_reset.set()
        self._tasks_finished.set()

    async def _handle_ui(self):
        while not self._exit:
            await self._next_move_available.wait()
            self._next_move_available.clear()
            await self._next_move
        self._tasks_finished.set()  
    
    async def _drive_random_enc(self):
        while True:
            await asyncio.sleep(600)
            self._random_enc_needed.set()
        self._tasks_finished.set()  

    async def _drive_advertise(self):
        while True:
            self.adv = asyncio.create_task(self.sm._bt.advertise())
            await self._advertise_reset.wait()
            self._advertise_reset.clear()
            self.adv.cancel()
            # self.adv = None
            await asyncio.sleep(2)
        self._tasks_finished.set()  

    async def background_task(self):
        tasks: list[asyncio.Task] = [
            asyncio.create_task(self._await_random_enc()),
            asyncio.create_task(self._handle_ui()),
            asyncio.create_task(self._drive_random_enc()),
            #asyncio.create_task(self._drive_advertise()),
            #asyncio.create_task(self._await_trainer()),
            ]
        await self._tasks_finished.wait()
        for t in tasks:
            t.cancel()
        if self.adv:
            self.adv.cancel()
