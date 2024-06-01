from asyncio import Event
import asyncio

from ..game.game_context import GameContext

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
                    ("Credits", ("Credits", [
                        ("Made by:", lambda: self._get_answer("REOPEN")),
                        ("Molive", lambda: self._get_answer("https://mo.molive.live/")),
                        ("Nyaalex", lambda: self._get_answer("REOPEN")),
                        ("plaaosert", lambda: self._get_answer("https://plaao.net/")),
                        ("Rynkitty", lambda: self._get_answer("REOPEN")),
                        ("Special Thanks:", lambda: self._get_answer("REOPEN")),
                        ("Badge Team", lambda: self._get_answer("https://tildagon.badge. emfcamp.org")),
                        ("Curtis P-F", lambda: self._get_answer("https://cpf.sh/")),
                        ("Skyler Msfld", lambda: self._get_answer("REOPEN")),
                        ("GCHQ.NET", lambda: self._get_answer("https://gchq.net /claim/badgemon")),
                        ("You!", lambda: self._get_answer("<3")),
                    ])),
                    ("Quit App", ("Quit App", [
                        ("Confirm", lambda: self._get_answer("QUIT"))
                    ]))
                ]
            ),
            no_exit=True
        )

    async def background_task(self):
        while True:
            await self.speech.write("Found a bug? Call MOLV!")
            await asyncio.sleep(0.5)
            if self.choice.closed_event.is_set():
                self.choice.open()
            await self._next_move_available.wait()
            self._next_move_available.clear()

            if self._next_move == "CONTINUE":
                await self.fade_to_scene(2)
                return
            elif self._next_move == "RESET":
                self.context = GameContext()
                await self.fade_to_scene(1)
                return
            elif self._next_move == "QUIT":
                await self.fade_to_scene(None)
                return
            elif self._next_move != "REOPEN":
                await self.speech.write(self._next_move)