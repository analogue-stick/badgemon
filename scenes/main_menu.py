from asyncio import Event

from ..scenes.scene import Scene

class MainMenu(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._next_move_available = Event()
        self._next_move = None
        self._gen_main_menu_dialog()

    def _get_answer(self, ans: str):
        self._next_move = ans
        self._next_move_available.set()

    def _gen_main_menu_dialog(self):
        last_chance = ("New Game", [("LAST CHANCE!", ("New Game", [("Reset Game", lambda: self._get_answer("RESET"))]))])
        self.choice.set_choices(
            (
                "BadgeMon",
                [
                    ("Continue", lambda: self._get_answer("CONTINUE")),
                    ("New Game", ("New Game", [
                        ("ARE YOU SURE??", ("New Game", [
                            ("ALL YOUR", last_chance),
                            ("BADGEMON", last_chance),
                            ("WILL DIE", last_chance),
                            ("FOREVER", last_chance),
                        ]))
                    ])),
                    ("Quit App", ("Quit App", [
                        ("Confirm", lambda: self._get_answer("QUIT"))
                    ]))
                ]
            ),
            no_exit=True
        )

    async def background_task(self):
        if self.choice._state == "CLOSED":
            await self.choice.open_and_wait()
        await self._next_move_available.wait()
        self._next_move_available.clear()

        if self._next_move == "CONTINUE":
            await self.fade_to_scene(2)
        elif self._next_move == "RESET":
            await self.fade_to_scene(1)
        elif self._next_move == "QUIT":
            await self.fade_to_scene(None)