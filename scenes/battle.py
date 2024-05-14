from ..scenes.scene import Scene
from system.eventbus import eventbus
from events.input import ButtonDownEvent
from ..util.misc import *
from ..util.animation import AnimLerp, AnimSin

from ..config import *

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

def draw_mon(ctx: Context, monIndex: int, x: float, y: float, flipx: bool, flipy: bool, scale: int):
    ctx.image_smoothing = 0
    if flipx:
        xscale = -1
    else:
        xscale = 1
    if flipy:
        yscale = -1
    else:
        yscale = 1
    ctx.scale(xscale,yscale)
    ctx.translate(x, y)
    ctx.image(ASSET_PATH+f"mons/mon-{monIndex}.png", 0, 0, 32*scale, 32*scale)
    ctx.translate(-x,-y)
    ctx.scale(xscale,yscale)

class Battle(Scene):
    def _set_text_tilt(self, x):
        self._text_tilt = x/16.0
    
    def __init__(self, *args, opponent: Player, **kwargs):
        super().__init__(*args, **kwargs)
        self.context.player.get_move = self._get_move
        self.context.player.get_new_badgemon = self._get_new_badgemon
        self._battle_context = BContext(self.context.player, opponent, True, self.speech)
        self._next_move: Mon | Item | Move | None = None
        self._next_move_available = Event()
        self._gen_choice_dialog()
        self._text_tilt = 0
        self.animation_scheduler.trigger(AnimSin(AnimLerp(editor=lambda x: self._set_text_tilt(x)), length=3000))

    def _gen_choice_dialog(self):
        self.choice.set_choices(
            (
                "BATTLE?!",
                [
                    ("Attack", ("Attack", [
                        (m.name, lambda: self._do_move(m)) for m in self._battle_context.mon1.moves
                    ])),
                    ("Item", ("Item", [
                        (f"{count}x {item.name}",lambda: self._do_item(i,item, count)) for (i,(item,count)) in filter(lambda i: i[1][0].usable_in_battle and i[1][1] > 0, enumerate(self._battle_context.player1.inventory))
                    ])),
                    ("Swap Mon", ("Swap Mon", [
                        (m.nickname,lambda: self._do_mon(m)) for m in filter(lambda b: not b.fainted, self._battle_context.player1.badgemon)
                    ])),
                    ("Run Away", ("Run Away??", [
                        ("Confirm", lambda: self._run_away())
                    ]))
                ]
            )
        )

    def _gen_new_badgemon_dialog(self):
        self.choice.set_choices(
            ("NEW BDGMON?!", [
                (m.nickname,lambda: self._do_mon(m)) for m in filter(lambda b: not b.fainted, self._battle_context.player1.badgemon)
            ]),
            True
        )

    def _handle_buttondown(self, event: ButtonDownEvent):
        if self._battle_context.turn and not self.choice.is_open() and not self.speech.is_open():
            self._gen_choice_dialog()
            self.choice.open()

    def _draw_mons(self, ctx: Context):
        draw_mon(ctx, self._battle_context.mon2.template.sprite, 0, -(32*3), False, False, 3)
        draw_mon(ctx, self._battle_context.mon1.template.sprite, 0, 0, True, False, 3)

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
        print("DO MOVE")
        self._next_move = move
        self._next_move_available.set()

    def _run_away(self):
        self._next_move = None
        self._next_move_available.set()
    
    def _do_item(self, index: int, item: Item, count: int):
        count -= 1
        if count == 0:
            self._battle_context.player1.inventory.pop(index)
        else:
            self._battle_context.player1.inventory[index] = (item, count)  # decrease stock
        self._next_move = item
        self._next_move_available.set()
        
    def _do_mon(self, mon: Mon):
        self._next_move = mon
        self._next_move_available.set()

    async def _get_move(self, mon):
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
    
    def scene_start(self):
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self.sm)
        return super().scene_start()
    
    def scene_end(self):
        eventbus.remove(ButtonDownEvent, self._handle_buttondown, self.sm)
        return super().scene_end()
    
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

            if isinstance(action, Move):
                print(f"USING MOVE {action}")
                await self._battle_context.use_move(player_mon, target_mon, action)

            elif isinstance(action, Mon):
                if self._battle_context.turn:
                    self._battle_context.mon1 = action
                else:
                    self._battle_context.mon2 = action

            elif isinstance(action, Item):
                action.function_in_battle(curr_player, self._battle_context, player_mon, target_mon)

            elif action is None:
                await self.speech.write(f"{curr_target.name} wins by default!")
                await self.fade_to_scene(2)
                return

            self._battle_context.turn = not self._battle_context.turn