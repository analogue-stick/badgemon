import math
import random

from . import constants

try:
    from sys import implementation as _sys_implementation
    if _sys_implementation.name != "micropython":
        from typing import Callable, List, Union, TYPE_CHECKING, Tuple
        if TYPE_CHECKING:
            from .battle_main import Battle
            from .mons import Mon
            MoveSpecial = Callable[['Battle', 'Mon', 'Mon', int], bool]
except ImportError:
    pass

from ..util.animation import Animation, AnimationEvent
from ..util import animation
from ..util.misc import shrink_until_fit, ASSET_PATH
from asyncio import Event
from ctx import Context
from app import App

class MoveAnim(Animation):
    def __init__(self, *args, app: App, draw_user = True, draw_target = True, user_pos: Tuple[float, float] = (0,0), target_pos: Tuple[float, float] = (0,0), user: 'Mon' = None, target: 'Mon' = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._draw_user = draw_user
        self._draw_target = draw_target
        self._user_pos = user_pos
        self._target_pos = target_pos
        self._user = user
        self._target = target
        self._time = 0
        self._app = app

    def on_anim_end(self) -> None:
        self._app.overlays.remove(self)
        self._app._scene._draw_target = True
        self._app._scene._draw_user = True
        return super().on_anim_end()
    
    def on_anim_start(self) -> None:
        self._app.overlays.append(self)
        self._app._scene._draw_target = self._draw_target
        self._app._scene._draw_user = self._draw_user
        return super().on_anim_start()

    def _update(self, time: float) -> None:
        self._time = time

    def draw(self, ctx: Context) -> None:
        pass

class SlanderAnim(MoveAnim):
    def __init__(self, *args, length=3000, **kwargs) -> None:
        insults = ["SUCKS", "IS BAD", "STINKS"]
        self.insult = random.choice(insults)
        super().__init__(*args, length, **kwargs)

    def draw(self, ctx: Context) -> None:
        if self._time < 0.33:
            rot = animation.lerp(0,math.tau*3.95,self._time*3.0)
            scale = animation.lerp(time=self._time*3.0)
        else:
            scale = 1
            rot = math.tau*3.95
        if self._time > 0.75:
            fade = animation.lerp(1,0,(self._time-0.75)*4)
        else:
            fade = 1
        
        ctx.rotate(rot)
        ctx.scale(scale,scale)
        ctx.rectangle(-50,-50,100,100).rgba(1,1,1,fade).fill()
        ctx.rectangle(-50,-50,100,100).rgba(0,0,0,fade).stroke()
        for i in range(5):
            ctx.move_to(-40, 10*i).line_to(40,10*i).stroke()
        ctx.text_align = Context.CENTER
        ctx.text_baseline = Context.MIDDLE
        name = self._target.nickname.upper()
        shrink_until_fit(ctx, name, 90, 60)
        ctx.move_to(0,-35).text(name)
        shrink_until_fit(ctx, self.insult, 90, 60)
        ctx.move_to(0,-15).text(self.insult)

class ScratchAnim(MoveAnim):
    def __init__(self, *args, length=500, **kwargs) -> None:
        super().__init__(*args, length, **kwargs)
    
    def draw(self, ctx: Context) -> None:
        end = animation.slower(x=self._time)
        start = animation.faster(x=self._time)
        for i in range(3):
            start_point_x = self._target_pos[0] + 15-i*30
            end_point_x = self._target_pos[0] + 45-i*30
            start_point_y = self._target_pos[1] + 45-i*15
            end_point_y = self._target_pos[1] + -45-i*15
            ctx.move_to(animation.lerp(start_point_x, end_point_x, start), animation.lerp(start_point_y, end_point_y, start))\
                .line_to(animation.lerp(start_point_x, end_point_x, end), animation.lerp(start_point_y, end_point_y, end))\
                .rgb(0.8,0.2,0.2).stroke()
            
class DevourAnim(MoveAnim):
    def __init__(self, *args, length=4000, **kwargs) -> None:
        self.image = ASSET_PATH+"moves/devour-"+str(random.randrange(3))+".jpg"
        super().__init__(*args, length, **kwargs)

    def draw(self, ctx: Context) -> None:
        ctx.image_smoothing = 0
        ctx.image(self.image, -120, -120, 240, 240)
        text_pos = animation.lerp(0, -600, self._time)
        ctx.text_align = Context.LEFT
        ctx.text_baseline = Context.MIDDLE
        ctx.font_size = 60
        ctx.rgb(1,1,1).move_to(text_pos,0).text("Censored... Please stand by...")

class MoveOverrideSpecial:
    """
    Any overrides that can't be expressed, even by MoveEffect.

    Example: a move that has power based on some specific stat
    """
    NO_OVERRIDE = 0


class MoveEffect:
    """
    Special effects called when moves are used, to do things aside from just dealing damage.
    Works as a nested set of functions.

    Objects can be instantiated using the MoveEffect static method (for prebuilt functions)
    or by writing a custom function with the signature:
    function(battle: battle_main.Battle, user: mons.Mon, target: mons.Mon, damage: int)

    To chain effects together (e.g. to deal 20% recoil damage then apply the BURNING status effect),
    use "then()" on a MoveEffect object.
    """
    @staticmethod
    def apply_status_effect(status: constants.StatusEffect, chance_to_apply: float = 1) -> "MoveEffect":
        """
        Applies a status effect at a specific chance. Success is if the effect is applied successfully
        (roll success AND effect successfully added)

        :param status: The status to apply to the target.
        :param chance_to_apply: The chance that status is applied.
        :return: A MoveEffect object containing this effect only.
        """
        async def function(battle: 'Battle', user: 'Mon', target: 'Mon', damage: int):
            if random.random() < chance_to_apply:
                return await battle.inflict_status(user, target, status)

            return False

        return MoveEffect(function)

    @staticmethod
    def recoil_damage(pct: float) -> "MoveEffect":
        """
        Deals self-damage equal to a percentage of the original damage (expected damage if missed)
        :param pct: The amount of damage to deal back to the user.
        :return: A MoveEffect object containing this effect only.
        """
        async def function(battle: 'Battle', user: 'Mon', target: 'Mon', damage: int):
            await battle.deal_damage(
                user, target, math.floor(damage * pct), None, "{target} took {damage_taken} recoil damage!"
            )
            return True

        return MoveEffect(function)

    @staticmethod
    def animation(Anim: MoveAnim) -> "MoveEffect":
        """
        Plays an animation in full before continuing.
        :param anim: The Animation
        :return: A MoveEffect object containing this effect only.
        """
        async def function(battle: 'Battle', user: 'Mon', target: 'Mon', damage: int):
            if user == battle.mon1:
                user_pos, target_pos = (-16*3, (16*3)-10), (16*3, -(16*3)+10)
            else:
                target_pos, user_pos = (-16*3, (16*3)-10), (16*3, -(16*3)+10)

            anim = Anim(app=battle._app, user_pos=user_pos, target_pos=target_pos, user = user, target = target)
            event = Event()
            anim.and_then(AnimationEvent(event))
            battle._app._animation_scheduler.trigger(anim)
            await event.wait()
            return True

        return MoveEffect(function)

    def _extend_with_condition(
            self, new_fn: Union['MoveSpecial', "MoveEffect"], valid_outcomes: List) -> "MoveEffect":
        """
        Appends new_fn to this object under the condition that the previous action returned one of valid_outcomes.
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :param valid_outcomes: A list of the valid outcomes (true or false). "Always" is [True, False].
        :return: This object.
        """
        old_fn = self.action

        new_fn_checked = new_fn
        if isinstance(new_fn, MoveEffect):
            new_fn_checked = new_fn.action

        async def new_action(battle: 'Battle', user: 'Mon', target: 'Mon', damage: int) -> bool:
            outcome = await old_fn(battle, user, target, damage)
            if outcome in valid_outcomes:
                return await new_fn_checked(battle, user, target, damage)

            return False

        self.action = new_action
        return self

    def __init__(self, action: 'MoveSpecial'):
        self.action = action

    def then(self, new_fn: Union['MoveSpecial', "MoveEffect"]):
        """
        Appends new_fn to this object so that it runs after this object's action.
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :return: This object.
        """
        return self._extend_with_condition(new_fn, [True, False])

    def then_if_failed(self, new_fn: Union['MoveSpecial', "MoveEffect"]):
        """
        Appends new_fn to this object so that it runs after this object's action, but only if the previous action failed
         (returned false).
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :return: This object.
        """
        return self._extend_with_condition(new_fn, [False])

    def then_if_success(self, new_fn: Union['MoveSpecial', "MoveEffect"]):
        """
        Appends new_fn to this object so that it runs after this object's action, but only if the previous action
         succeeded (returned true).
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :return: This object.
        """
        return self._extend_with_condition(new_fn, [True])

    async def execute(self, battle: 'Battle', user: 'Mon', target: 'Mon', damage: int):
        """
        Do it. Call this when the move is used - after damage is calculated and dealt. If the move missed, still call
         this, but use the predicted damage rather than the actual damage.
        :param battle: The current battle.
        :param user: The user of the move.
        :param target: The target of the move.
        :param damage: The amount of damage the move dealt (or would have done, in the case of a miss)
        :return:
        """
        await self.action(battle, user, target, damage)


class Move:
    id_inc = 0

    def __init__(
        self, name: str, desc: str, move_type: constants.MonType, max_pp: int, power: int, accuracy: int,
        effect_on_hit: MoveEffect = None, effect_on_miss: MoveEffect = None,
            special_override: MoveOverrideSpecial = MoveOverrideSpecial.NO_OVERRIDE,
            animation = None
    ):
        """
        Any kind of move.
        :param name: The name of the move.
        :param desc: The description of the move.
        :param move_type: The damage type of the move.
        :param max_pp: The maximum PP of the move. The move's PP is reset to this on a full heal.
        :param power: Analogous to Pokémon move power, e.g. tackle is 40 power, hyper beam is 150.
        :param accuracy: 0-100 (it's a percentage)
        :param effect_on_hit: Special effect called when the move hits.
        :param effect_on_miss: Special effect called when the move misses.
        :param special_override: Any override that a special case must be made for.
        """
        self.id = Move.id_inc
        Move.id_inc += 1

        self.name = name
        self.desc = desc
        self.move_type = move_type
        self.max_pp = max_pp
        self.power = power
        self.accuracy = accuracy
        self.effect_on_hit = effect_on_hit
        self.effect_on_miss = effect_on_miss
        self.special_override = special_override
        self.animation = animation


moves_list = [
    Move('Scratch', 'Scratches opponent', constants.MonType.NORMAL, 35, 40, 100, MoveEffect.animation(ScratchAnim)),
    Move('Tackle', "A crude body slam.", constants.MonType.NORMAL, 35, 40, 100),
    Move('Bite', "The user bites the opponent.", constants.MonType.NORMAL, 35, 40, 100),
    Move('Slap', "A quick slap to the opponent's face.", constants.MonType.NORMAL, 35, 40, 100),
    Move('PleadingFace', "The user looks pathetically at the opponent, reducing their ATK and SpATK.", constants.MonType.NORMAL, 35, 40, 100),
    Move('Scowl', "The user fixes a withering scowl at the opponent, sharply reducing their DEF.", constants.MonType.NORMAL, 35, 40, 100),
    Move('Think', "The user ponders deeply, gaining an increase to SpATK and SpDEF.", constants.MonType.NORMAL, 35, 40, 100),
    Move('PsychUp', "The user repeats some words of self-encouragement, gaining an increase to ATK and SpATK.", constants.MonType.FIGHTING, 35, 40, 100),
    Move('free()', "Deallocates the space previously allocated to the opponent", constants.MonType.BUG, 35, 40, 100),
    Move('StackSmash', "Writes a \'normal amount of data\' to the opponent's stack.", constants.MonType.BUG, 35, 40, 100),
    Move('SQLInject', "Writes a \'normal\' string to the opponent's database';DROP TABLE HP", constants.MonType.BUG, 35, 40, 100),
    Move('WetFish', "The opponent is hit across the face with a wet fish", constants.MonType.WATER, 35, 40, 100),
    Move('ScathingInsult', "Make a witty remark about the opponent's mother.", constants.MonType.NORMAL, 35, 40, 100),
    Move('Pandemic', "Cancels opponent due to pandemic restrictions", constants.MonType.GHOST, 35, 40, 100),
    Move('TorrentialRain', "Maybe if the opponent had pitched at the top of the hill they would still be fine right now", constants.MonType.WATER, 35, 40, 100),
    Move('ICBM', "This feels self explanatory.", constants.MonType.NORMAL, 35, 40, 100),
    Move('Mallet', "Hits opponent with comically large mallet", constants.MonType.FIGHTING, 35, 40, 100),
    Move('Rework', "Rework the opponent into a stylish broach", constants.MonType.STEEL, 35, 40, 100),
    Move('Slander', "Run a smear campain against the opponent in the local newspaper.", constants.MonType.NORMAL, 35, 40, 100, MoveEffect.animation(SlanderAnim)),
    Move('Nose!', "Get your opponent's nose.", constants.MonType.NORMAL, 35, 40, 100),
    Move('DangerHug', "Gives opponent a (deadly) hug.", constants.MonType.NORMAL, 35, 40, 100),
    Move('PinchCheeks', "Pinch the opponent's cheeks and tell them how much they've grown.", constants.MonType.NORMAL, 35, 40, 100),
    Move('MailFraud', "All items applied to the opponent for 2 turns will be appllied to you instead.", constants.MonType.NORMAL, 35, 40, 100),
    Move('Intoxicate', "Gets opponent drunk.", constants.MonType.POISON, 35, 40, 100),
    Move('Irrationalise', "Use advanced mathematics to prove that the opponent is irrational, and therefore not representable as a fraction.", constants.MonType.PSYCHIC, 35, 40, 100),
    Move('Rawr', "OwO? *nuzzles opponent*", constants.MonType.DRAGON, 35, 40, 100),
    Move('Uppercut', "Pow! Blam! Wham! Slap! Ka-pow!", constants.MonType.FIGHTING, 35, 40, 100),
    Move('Disassemble', "Disassembles the opponent to look for vulnerabilities.", constants.MonType.DRAGON, 35, 40, 100),
    Move('Arson', "Did you know that the opponent is flammable?", constants.MonType.FIRE, 35, 40, 100),
    Move('Tazer', "The power of the sun in the palm of your hand.", constants.MonType.ELECTRIC, 35, 40, 100),
    Move('FlamingSword', "Its cool factor more than makes up for its impractibility.", constants.MonType.FIRE, 35, 40, 100),
    Move('Duel', "Challenge opponent to pistol duel", constants.MonType.DARK, 35, 40, 100),
    Move('FP16', "Cast the opponent to a smaller data type, making them less accurate.", constants.MonType.BUG, 35, 40, 100),
    Move('ShakeHands', "Shake hands with the opponent and recover 50% HP each.", constants.MonType.NORMAL, 35, 40, 100),
    Move('OOOooOOoO!', "Spook opponent", constants.MonType.GHOST, 35, 40, 100),
    Move('Overvolt', "Send more than the rated voltage to the opponent's VCC pin.", constants.MonType.ELECTRIC, 35, 40, 100),
    Move('Drain', "Reduce the opponent's voltage potential.", constants.MonType.GROUND, 35, 40, 100),
    Move('DodgyCurry', "Serve the opponent a dodgy curry.", constants.MonType.POISON, 35, 40, 100),
    Move('Bury', "Covers opponent in a layer of dirt", constants.MonType.GROUND, 35, 40, 100),
    Move('FancyLighting', "Blind opponent using dope ass lightshow", constants.MonType.GHOST, 35, 40, 100),
    Move('WTF?', "Shows the opponent the \'WTF?\' talk.", constants.MonType.PSYCHIC, 35, 40, 100),
    Move('FineMist', "Gives opponent a light misting.", constants.MonType.WATER, 35, 40, 100),
    Move('UnexpectedBill', "Gives opponent a large shock.", constants.MonType.ELECTRIC, 35, 40, 100),
    Move('Devour', "Attempt to eat opponent. You cannot eat Rinoa.", constants.MonType.NORMAL, 35, 40, 100, MoveEffect.animation(DevourAnim)),
    Move('DadJoke', "Tell a dad joke to the opponent, who cringes so hard they deal themselves damage.", constants.MonType.PSYCHIC, 35, 40, 100)
]