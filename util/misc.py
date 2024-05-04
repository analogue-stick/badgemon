from ctx import Context

def ctx_line(self: Context, x: float, y: float, x2: float, y2: float):
    return self.move_to(x,y).line_to(x2,y2)