from ..scenes.scene import Scene
from events.input import ButtonDownEvent
from ..util.misc import *
from ..util.animation import AnimLerp, AnimSin

from ..game.mons import Mon, mons_list
from ..game.items import Item, items_list
from ..game.moves import Move
from ..game.battle_main import Battle as BContext
from ..game.player import Cpu, Player
from ctx import Context

from ..game import constants

from asyncio import Event

potion = items_list[0]
mon_template1 = mons_list[0]
mon_template2 = mons_list[1]
mon1 = Mon(mon_template1, 5).set_nickname("small guy")
mon2 = Mon(mon_template2, 17).set_nickname("mr. 17")
mon3 = Mon(mon_template1, 17).set_nickname("David")
mon4 = Mon(mon_template2, 33).set_nickname("large individual")
mon5 = Mon(mon_template1, 100).set_nickname("biggest dude")

class Battle(Scene):
    def _set_text_tilt(self, x):
        self._text_tilt = x/16.0
    
    def __init__(self, *args, opponent: Player, **kwargs):
        super().__init__(*args, **kwargs)
        self.context.player.get_move = self._get_move
        self.context.player.get_new_badgemon = self._get_new_badgemon
        self.context.player.gain_badgemon = self._gain_badgemon
        self._battle_context = BContext(self.context.player, opponent, True, self.sm, self.speech)
        self._next_move: Mon | Item | Move | self.Desc | None = None
        self._next_move_available = Event()
        self._gen_choice_dialog()
        self._text_tilt = 0
        self._draw_user = True
        self._draw_target = True
        self.animation_scheduler.trigger(AnimSin(AnimLerp(editor=lambda x: self._set_text_tilt(x)), length=3000))

    def _gen_choice_dialog(self):
        available_moves: set[Move] = set()
        for m in self._battle_context.player1.badgemon:
            if not m.fainted:
                available_moves.update(m.moves)
        self.choice.set_choices(
            (
                "BATTLE?!",
                [
                    ("Attack", ("Attack", [
                        (m.name, self._do_move(m)) for m in self._battle_context.mon1.moves
                    ])),
                    ("Item", ("Item", [
                        (f"{count}x {item.name}", self._do_item(item, count)) for (item,count) in self._battle_context.player1.inventory.items() if item.usable_in_battle and count > 0
                    ])),
                    ("Swap Mon", ("Swap Mon", [
                        (m.nickname, self._do_mon(m)) for m in self._battle_context.player1.badgemon if not m.fainted
                    ])),
                    ("Describe...", ("Describe...", [
                        ("Item", ("Describe Item", [(i.name, self._describe(i)) for i,c in self._battle_context.player1.inventory.items() if i.usable_in_battle and c > 0])),
                        ("Move", ("Describe Move", [(m.name, self._describe(m)) for m in available_moves]))
                    ])),
                    ("Run Away", ("Run Away??", [
                        ("Confirm", self._run_away())
                    ]))
                ]
            )
        )

    def _gen_new_badgemon_dialog(self):
        self.choice.set_choices(
            ("NEW BDGMON?!", [
                (m.nickname, self._do_mon(m)) for m in self._battle_context.player1.badgemon if not m.fainted
            ]),
            True
        )

    def handle_buttondown(self, event: ButtonDownEvent):
        if self._battle_context.turn and not self.choice.is_open() and not self.speech.is_open() and not self.text.is_open():
            self._gen_choice_dialog()
            self.choice.open()

    def _draw_mons(self, ctx: Context):
        if self._draw_target:
            draw_mon(ctx, self._battle_context.mon2.template.sprite, 0, -(32*3)+10, False, False, 3)
        if self._draw_user:
            draw_mon(ctx, self._battle_context.mon1.template.sprite, 0, -10, True, False, 3)

    def _draw_health(self, ctx: Context):
        x = 10
        y = 30
        width  = 85 
        radius = 10
        border = 3
        
        other_health = (self._battle_context.mon2.hp / self._battle_context.mon2.stats[constants.STAT_HP])
        us_health = (self._battle_context.mon1.hp / self._battle_context.mon1.stats[constants.STAT_HP])

        ctx.gray(0)
        ctx.round_rectangle(-x-width-border, -y-border, width+border*2, radius+border*2, radius).fill()
        ctx.round_rectangle(x-border, y-border-radius, width+border*2, radius+border*2, radius).fill()
        ctx.rgb((0.7*(1-other_health))+0.2,(0.7*other_health)+0.2,0.2)
        ctx.round_rectangle(-x-(width*other_health), -y, width * other_health, radius, radius).fill()
        ctx.rgb((0.7*(1-us_health))+0.2,(0.7*us_health)+0.2,0.2)
        ctx.round_rectangle(x, y-radius, width*us_health, radius, radius).fill()

    def _draw_names(self, ctx: Context):
        x = 10
        y = 45

        ctx.gray(0)
        ctx.font_size = 20
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.RIGHT
        shrink_until_fit(ctx, self._battle_context.mon2.nickname, 90)
        ctx.move_to(-x,-y).text(self._battle_context.mon2.nickname)
        ctx.text_align = Context.LEFT
        shrink_until_fit(ctx, self._battle_context.mon1.nickname, 90)
        ctx.move_to(x,y).text(self._battle_context.mon1.nickname)

    def _your_turn(self, ctx: Context):
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.CENTER
        ctx.font_size = 24
        ctx.rgb(0.8,0.4,0.2)
        gap = 0.165

        ctx.rotate(gap*-1.5+self._text_tilt)
        ctx.move_to(0, -100).text("Y")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("O")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("U")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("R")

        ctx.move_to(0, 100).text("T")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("U")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("R")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("N")
        ctx.rotate(gap*1.5-self._text_tilt)
        ctx.line_width = 5
        ctx.arc(0,0,115,0,6.28,0).stroke()

    def _their_turn(self, ctx: Context):
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.CENTER
        ctx.font_size = 24
        ctx.rgb(0.2,0.4,0.8)
        gap = 0.165
        ctx.rotate(gap*-2+self._text_tilt)
        ctx.move_to(0, -100).text("T")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("H")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("E")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("I")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("R")
        ctx.rotate(gap*-0.5)

        ctx.move_to(0, 100).text("T")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("U")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("R")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("N")
        ctx.rotate(gap*1.5-self._text_tilt)
        ctx.line_width = 5
        ctx.arc(0,0,115,0,6.28,0).stroke()

    def draw(self, ctx: Context):
        super().draw(ctx)
        self._draw_mons(ctx)
        self._draw_health(ctx)
        self._draw_names(ctx)
        if self._battle_context.turn:
            self._your_turn(ctx)
        else:
            self._their_turn(ctx)

    def _do_move(self, move: Move):
        def f():
            self._next_move = move
            self._next_move_available.set()
        return f

    def _run_away(self):
        def f():
            self._next_move = None
            self._next_move_available.set()
        return f
    
    def _do_item(self, item: Item, count: int):
        def f():
            if item.name != "Badgemon Doll":
                nc = count - 1
                if nc == 0:
                    self._battle_context.player1.inventory.pop(item)
                else:
                    self._battle_context.player1.inventory[item] = nc  # decrease stock
            self._next_move = item
            self._next_move_available.set()
        return f
        
    def _do_mon(self, mon: Mon):
        def f():
            self._next_move = mon
            self._next_move_available.set()
        return f
    
    class Desc():
        def __init__(self, t):
            self.t = t

        def __str__(self) -> str:
            return self.t.desc
    
    def _describe(self, thing):
        def f():
            self._next_move = self.Desc(thing)
            self._next_move_available.set()
        return f

    async def _get_move(self, mon: Mon):
        self._gen_choice_dialog()
        print("AWAITING MOVE")
        await self._next_move_available.wait()
        self._next_move_available.clear()
        return self._next_move
    
    async def _get_new_badgemon(self):
        self._gen_new_badgemon_dialog()
        await self._next_move_available.wait()
        self._next_move_available.clear()
        return self._next_move
    
    async def _gain_badgemon(self, mon: Mon, case, badgedex):
        await self.speech.write("What will you name them? Enter nothing for a default.")
        mon.nickname = await self.text.wait_for_answer("Nickname?", mon.nickname)
        case.append(mon)
        badgedex.find(mon.template.id)
        await self.speech.write(f"{mon.nickname} has been added to your badgemon case!")
    
    async def background_task(self):
        print("test")
        while True:
            if self._battle_context.turn:
                curr_player, curr_target = self._battle_context.player1, self._battle_context.player2
                player_mon, target_mon = self._battle_context.mon1, self._battle_context.mon2
            else:
                curr_player, curr_target = self._battle_context.player2, self._battle_context.player1
                player_mon, target_mon = self._battle_context.mon2, self._battle_context.mon1

            print("target faint?")
            
            if target_mon.fainted:
                await self.speech.write(f"{target_mon.nickname} fainted!")
                all_fainted = True
                for mon in curr_target.badgemon:
                    all_fainted = all_fainted and mon.fainted
                if all_fainted:
                    await self.speech.write(f"{curr_player.name} wins!")
                    await self.fade_to_scene(2)
                    return
                else:
                    new_badgemon = await curr_target.get_new_badgemon()
                    if self._battle_context.turn:
                        self._battle_context.mon2 = new_badgemon
                    else:
                        self._battle_context.mon1 = new_badgemon
                    target_mon = new_badgemon

            print("player faint?")

            if player_mon.fainted:
                await self.speech.write(f"{player_mon.nickname} fainted!")
                all_fainted = True
                for mon in curr_player.badgemon:
                    all_fainted = all_fainted and mon.fainted
                if all_fainted:
                    await self.speech.write(f"{curr_target.name} wins!")
                    await self.fade_to_scene(2)
                    return
                else:
                    new_badgemon = await curr_player.get_new_badgemon()
                    if self._battle_context.turn:
                        self._battle_context.mon1 = new_badgemon
                    else:
                        self._battle_context.mon2 = new_badgemon
                    player_mon = new_badgemon

            print("getting move")

            action = await curr_player.get_move(player_mon)

            print(f"move got: {action}")

            same_turn = False

            if isinstance(action, Move):
                print(f"USING MOVE {action}")
                await self._battle_context.use_move(player_mon, target_mon, action)

            elif isinstance(action, Mon):
                if self._battle_context.turn:
                    self._battle_context.mon1 = action
                else:
                    self._battle_context.mon2 = action

            elif isinstance(action, Item):
                if action.name == "Badgemon Doll":
                    if self._battle_context.turn:
                        await self.speech.write(f"{player_mon.nickname} appreciated the craftsmanship of the doll.")
                    same_turn = True
                await self.speech.write(f"Used {action.name}!") 
                if action.name.endswith("HexBox"):
                    if not isinstance(self._battle_context.player2, Cpu):
                        await self.speech.write("Oh no! You can't catch THAT Badgemon!")
                    else:
                        catch = await self._battle_context.catch(curr_player, player_mon, target_mon, action)
                        if catch:
                            print("CATCH")
                            await curr_player.gain_badgemon(target_mon, curr_player.badgemon_case, curr_player.badgedex)
                            await self.fade_to_scene(2)
                            return
                else:
                    action.function_in_battle(curr_player, self._battle_context, player_mon, target_mon)

            elif isinstance(action, self.Desc):
                if self._battle_context.turn:
                    if isinstance(action.t, Move):
                        await self.speech.write(f"|TYPE: {constants.type_to_str(action.t.move_type)}| {action}")
                    else:
                        await self.speech.write(str(action))
                same_turn = True

            elif action is None:
                await self.speech.write(f"{curr_target.name} wins by default!")
                await self.fade_to_scene(2)
                return

            if not same_turn:
                self._battle_context.turn = not self._battle_context.turn