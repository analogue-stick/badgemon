from ctx import Context
from ..config import ASSET_PATH
import sys

def ctx_line(self: Context, x: float, y: float, x2: float, y2: float):
    return self.move_to(x,y).line_to(x2,y2)

def shrink_until_fit(ctx: Context, text: str, max_width: float, max_font: int = 20):
    width = max_font
    ctx.font_size = width
    while ctx.text_width(text) > max_width:
        width -= 1
        ctx.font_size = width
    return width

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

def dump_exception(e: Exception):
    if sys.implementation == "micropython":
        sys.print_exception(e)
    else:
        import traceback
        traceback.print_exception(e)