from ctx import Context

def ctx_line(self: Context, x: float, y: float, x2: float, y2: float):
    return self.move_to(x,y).line_to(x2,y2)

def shrink_until_fit(ctx: Context, text: str, max_width: float, max_font: int = 20):
    width = max_font
    ctx.font_size = width
    while ctx.text_width(text) > max_width:
        width -= 1
        ctx.font_size = width
