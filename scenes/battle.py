from ..main import Cpu
from system.eventbus import eventbus
from events.input import ButtonDownEvent
from ..util.speech import SpeechDialog
from ..util.choice import ChoiceDialog
from ..util.misc import *

from ..config import *

from ..game.mons import Mon, mons_list
from ..game.items import Item, items_list
from ..game.moves import Move
from ..game.battle_main import Battle as BContext
from ..game.battle_main import Actions
from ..game.player import Player
from ctx import Context

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

class Battle():
    def __init__(self, battle_context: BContext, debug: bool = False):
        if debug:
            player_a = Player("Scarlett", [mon2, mon3], [mon4], [(potion, 2)])
            player_a.get_move = self._get_move
            player_b = Cpu('Tr41n0rB0T', [mon1, mon5], [], [])
            self._battle_context = BContext(player_a, player_b, True)
            #TODO: self.battle_context.do_battle
        else:
            self._battle_context = battle_context
        self._speech = SpeechDialog(
            app=self,
            speech="Battle Testing!"
        )
        self._choice = ChoiceDialog(
            app=self,
            header="BATTLE?!"
        )
        self._next_move: Mon | Item | Move | None = None
        self._next_move_available = Event()
        self._gen_choice_dialog()
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self)

    def _gen_choice_dialog(self):
        self._choice.set_choices(
                    [
                ("Attack", [
                    (m.name,lambda a: a._do_move(m)) for m in self._battle_context.mon1.moves
                ]),
                ("Item", [
                    (f"{count}x {item.name}",lambda a: a._do_item(i,item, count)) for (i,(item,count)) in filter(lambda i: i[1][0].usable_in_battle and i[1][1] > 0, enumerate(self._battle_context.player1.inventory))
                ]),
                ("Swap Mon", [
                    (m.nickname,lambda a: a._do_mon(m)) for m in filter(lambda b: not b.fainted, self._battle_context.player1.badgemon)
                ]),
                ("Run Away", [
                    ("Confirm", lambda a: a._run_away())
                ])
            ],
            "BATTLE?!"
        )

    def _handle_buttondown(self, event: ButtonDownEvent):
        if not self._choice.is_open():
            self._gen_choice_dialog()
            self._choice.open()

    def update(self, delta: float):
        self._choice.update(delta)

    def _draw_background(self, ctx: Context):
        ctx.gray(0.9).rectangle(-120, -120, 240, 240).fill()

    def _draw_mons(self, ctx: Context):
        draw_mon(ctx, self._battle_context.mon2.template.sprite, 0, -(32*3), False, False, 3)
        draw_mon(ctx, self._battle_context.mon1.template.sprite, 0, 0, True, False, 3)

    def _draw_health(self, ctx: Context):
        x = 10
        y = 30
        width  = 85 
        radius = 10
        border = 3
        
        other_health = (self._battle_context.mon2.hp / self._battle_context.mon2.template.base_hp)
        us_health = (self._battle_context.mon1.hp / self._battle_context.mon1.template.base_hp)

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
        ctx.move_to(-x,-y).text(self._battle_context.mon2.nickname)
        ctx.text_align = Context.LEFT
        ctx.move_to(x,y).text(self._battle_context.mon1.nickname)

    def _your_turn(self, ctx: Context):
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.CENTER
        ctx.font_size = 24
        ctx.rgb(0.8,0.4,0.2)
        gap = 0.165

        ctx.rotate(gap*-1.5)
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
        ctx.rotate(gap*1.5)
        ctx.line_width = 5
        ctx.arc(0,0,115,0,6.28,0).stroke()

    def _their_turn(self, ctx: Context):
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.CENTER
        ctx.font_size = 24
        ctx.rgb(0.2,0.4,0.8)
        gap = 0.165

        ctx.rotate(gap*-2)
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
        ctx.rotate(gap*1.5)
        ctx.line_width = 5
        ctx.arc(0,0,115,0,6.28,0).stroke()

    def draw(self, ctx: Context):
        ctx.line = ctx_line
        self._draw_background(ctx)
        self._draw_mons(ctx)
        self._draw_health(ctx)
        self._draw_names(ctx)
        self._their_turn(ctx)
        self._choice.draw(ctx)

    def _do_move(self, move: Move):
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

    async def _get_move(self):
        await self._next_move_available.wait()
        self._next_move_available.clear()
        if isinstance(self._next_move, Mon):
            return (Actions.SWAP_MON, self._next_move)
        elif isinstance(self._next_move, Item):
            return (Actions.USE_ITEM, self._next_move)
        elif isinstance(self._next_move, Move):
            return (Actions.MAKE_MOVE, self._next_move)
        elif isinstance(self._next_move, None):
            return (Actions.RUN_AWAY, self._next_move)
        return (Actions.RUN_AWAY, None)