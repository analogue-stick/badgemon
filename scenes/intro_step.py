from app import App

class LoadingScreen(App):
    def __init__(self):
        self.load_start = False

    def update(self, delta):
        print(delta)
        if self.load_start:
            from system.scheduler import scheduler
            from ..scenes.scene_manager import SceneManager
            scheduler.start_app(SceneManager(), foreground=True)
            self.load_start = False
            scheduler.stop_app(self)

    def draw(self, ctx):
        ctx.rectangle(-120, -120, 240, 240).gray(0).fill()
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.gray(1).move_to(0,0).text("Loading...").fill()
        self.load_start = True