from asyncio import Event
from ..scenes.scene import Scene
from ctx import Context

class MainMenu(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._next_move_available = Event()
        self._next_move = None
        self._gen_main_menu_dialog()
        self.choice.open()

    def _get_answer(self, ans: str):
        self._next_move = ans
        self._gen_main_menu_dialog

    def _gen_main_menu_dialog(self):
        last_chance = [("LAST CHANCE!", lambda: self._get_answer("RESET"))]
        self.choice.set_choices(
                    [
                ("Continue", lambda: self._get_answer("CONTINUE")),
                ("New Game", [
                    ("ARE YOU SURE??", [
                        ("ALL YOUR", last_chance),
                        ("OLD BADGEMON", last_chance),
                        ("WILL DIE", last_chance),
                        ("FOREVER", last_chance),
                    ])
                ]),
                ("Quit App", [
                    ("Confirm", lambda: self._get_answer("QUIT"))
                ])
            ],
            "BadgeMon",
            no_exit=True
        )

    def draw(self, ctx: Context):
        self._draw_background(ctx)

    async def background_task(self):
        while True:
            print("getting move")

            action = await self._next_move_available.wait()
            self._next_move_available.clear()

            print(f"move got: {action}")

            if move == "CONTINUE":
                self.fade_to_scene(Field())
            elif move == "RESET":
                self.fade_to_scene(Intro())
            elif move == "QUIT":
                self.fade_to_scene(None)