from asyncio import Event, Task, create_task
from typing import Coroutine, Tuple

from ..game.player import Cpu

from ..scenes.scene import Scene
from ..game.items import Item, items_list
from ..game.mons import Mon, mons_list
from events.input import ButtonDownEvent
from system.eventbus import eventbus
from ctx import Context

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
        self._exit = False
        try:
            self._gen_field_dialog()
        except Exception as e:
            print(e)

    def _get_answer(self, ans: Coroutine, exit = False):
        return lambda: self._get_answer_internal(ans,exit)

    def _get_answer_internal(self, ans: Coroutine, exit = False):
        self._next_move = ans
        self._exit = exit
        self._next_move_available.set()

    async def _use_item(self, item: Item, count: int, mon: Mon):
        count -= 1
        if count == 0:
            self.inventory.pop(item)
        else:
            self.context.player.inventory[item] = count
        await self.speech.write(f"Using {item.name}!")
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
        await self.fade_to_scene(3, opponent=Cpu('Tr41n0rB0T', [mon1, mon5], [], []))

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
            m = min(self.context.player.money//item.value, 255-current)
            no_purchase &= m == 0
            max_purchase.append((item, m))
            
        if no_purchase:
            shop = self._get_answer(self.speech.write("You don't have enough money!"))
        else:
            shop = (f"GP: {self.context.player.money}", [(f"{item.name}",
                    (f"Buy {item.name}", [(f"{i}x {item.name}",
                            (f"Buy {i}x {item.name}", [("Confirm",
                                self._get_answer(self._purchase(item,i))
                            )])
                        ) for i in range(1,count+1)])
                    ) for (item, count) in max_purchase if count > 0])

        self.choice.set_choices(
            ("Field", [
                ("Badgemon", ("Badgemon",[
                    ("Heal Badgemon", self._get_answer(self._use_full_heal())),
                    ("Deposit BMon", swap_mon_out),
                    ("Withdraw BMon", swap_mon_in),
                    ("Change Order", swap_mons),
                ])),
                ("Item Bag", ("Item Bag", [
                    ("Use Item", use_item),
                    ("Describe Item", describe_item),
                    ("Buy Item", shop)
                ])),
                ("Main Menu", ("Main Menu?",[
                    ("Confirm", self._get_answer(self.fade_to_scene(0), True))
                ])),
                ("Instructions", self._get_answer(self.fade_to_scene(4), True)),
                ("Settings", ("Settings",[
                    ("Tog. RandEnc", self._get_answer(self._toggle_randomenc()))
                ])),
                ("Save", self._get_answer(self._save())),
                ("DEBUG BATTLE", self._get_answer(self._initiate_battle(), True))
            ])
        )

    def draw(self, ctx: Context):
        super().draw(ctx)

    def handle_buttondown(self, event: ButtonDownEvent):
        if not self.choice.is_open() and not self.speech.is_open():
            self._gen_field_dialog()
            self.choice.open()

    async def background_task(self):
        while not self._exit:
            await self._next_move_available.wait()
            self._next_move_available.clear()
            try:
                await self._next_move
            except Exception as e:
                print("NEXT MOVE FAIL")
                print(e)
                print(e.with_traceback(True))
                print(e)