from asyncio import Event
from ..scenes.scene import Scene
from system.eventbus import eventbus
from events.input import ButtonDownEvent
from ctx import Context

class Field(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._next_move_available = Event()
        self._next_move = None
        self._gen_field_dialog()

    def _get_answer(self, ans: str):
        self._next_move = ans
        self._next_move_available.set()

    def _gen_field_dialog(self):
        pick_mon = ()
        self.choice.set_choices(
                    [
                ("Badgemon", [
                    ("Heal Badgemon", self._use_full_heal),
                    ("Deposit Badgemon", )
                ]),
                ("New Game", [
                    ("ARE YOU SURE??", [
                        ("ALL YOUR", last_chance),
                        ("BADGEMON", last_chance),
                        ("WILL DIE", last_chance),
                        ("FOREVER", last_chance),
                    ])
                ]),
                ("Quit App", [
                    ("Confirm", lambda: self._get_answer("QUIT"))
                ])
            ],
            "Field"
        )

    def draw(self, ctx: Context):
        super().draw(ctx)

    def _handle_buttondown(self, event: ButtonDownEvent):
        if not self.choice.is_open() and not self.speech.is_open():
            self._gen_field_dialog()
            self.choice.open()

    async def background_task(self):
        await self.choice.open_and_wait()
        await self._next_move_available.wait()
        self._next_move_available.clear()
        
        if self._next_move == "CONTINUE":
            await self.fade_to_scene(Field)
        elif self._next_move == "RESET":
            await self.fade_to_scene(Intro)
        elif self._next_move == "QUIT":
            await self.fade_to_scene(None)
