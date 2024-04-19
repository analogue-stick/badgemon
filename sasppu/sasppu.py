from array import Array

class RotSprite():
    h = 0
    v = 1
    x = 2
    y = 3
    a = 4
    b = 5
    c = 6
    d = 7
    width_height = 8
    flags = 9
    class Flags():
        enabled = 0
        flipx   = 1
        flipy   = 2
        size    = 3 # 32x32 or 64x64
        main_screen = 4
        sub_screen = 5 # main screen or sub screen
        c_math  = 6 #enable color math
        priority = 7 # In front or behind background
        double = 8 # double size 

    stride = 10
    sprite_count = 4

class Sprite():
    x = 0
    y = 1
    width_height = 2
    flags = 3
    class Flags():
        enabled = 1
        flipx   = 2
        flipy   = 4
        #unused
        main_screen = 16
        sub_screen = 32 # main screen or sub screen
        c_math  = 64 #enable color math
        priority = 128 # In front or behind background
        double = 256 # double size
        #windowing
        in_window = 512
        out_window = 1024
        window_log1 = 2048
        window_log2 = 4096

    stride = 4
    sprite_count = 256

class SASPPU():
    screen = Array('H', [0]*240*240)

    mainscreen_colour: int = 0
    subscreen_colour: int = 0

    disable_backgound: bool = False

    background = Array('H', [0]*512*512)
    bgscrollh: int = 0
    bgscrollv: int = 0

    sprites = []

    half_main_screen = False
    double_main_screen = False
    half_sub_screen = False
    double_sub_screen = False
    add_sub_screen = False
    sub_sub_screen = False
    fade_enable = False
    screen_fade = 256
    cmath_enable = False

    bg0_in_window = False
    bg0_out_window = False
    bg0_window_log1 = False
    bg0_window_log2 = False

    window_1_left = 0
    window_1_right = 0
    window_2_left = 0
    window_2_right = 0

    main_sprite_cache = Array('B', [0]*16)
    sub_sprite_cache = Array('B', [0]*16)
    OAM = Array('H', [0]*Sprite.stride*Sprite.sprite_count)

    @micropython.viper
    def per_pixel(self, x: int, y: int):
        main = self.mainscreen_colour
        sub = self.subscreen_colour

        c_math = False
        window_1 = (x >= self.window_1_left and x <= self.window_1_right)
        window_2 = (x >= self.window_2_left and x <= self.window_2_right)

        oam = self.OAM
        cache = self.sprite_cache
        bg_handled = False
        for spr in range(16):
            index = cache[spr] * Sprite.stride
            flags = oam[index+Sprite.flags]
            if not (flags & Sprite.Flags.enabled):
                break
            if (flags & Sprite.Flags.priority) and not bg_handled:
                if not self.disable_backgound:
                    bg0 = self.background[((y+self.bgscrollv)&511)*512+((x+self.bgscrollh)&511)]
                    if bg0 != 0:
                        log1 = self.bg0_window_log1
                        log2 = self.bg0_window_log2
                        if log1 and log2:
                            window = window_1 == window_2
                        elif log1 and not log2:
                            window = window_1 != window_2
                        elif not log1 and log2:
                            window = window_1 and window_2
                        elif not log1 and not log2:
                            window = window_1 or window_2
                        if (window and self.bg0_in_window) or (not window and self.bg0_out_window):
                            main = bg0
                bg_handled = True
            double = (flags & Sprite.Flags.double) > 0
            sprite_width = oam[index+Sprite.width_height] >> 8
            if double:
                sprite_width <<= 1
            offsetx = x - oam[index+Sprite.x]
            if offsetx >= 0 and offsetx < sprite_width:
                if (flags & Sprite.Flags.flipx):
                    offsetx = sprite_width - offsetx
                offsety = y - oam[index+Sprite.y]
                if (flags & Sprite.Flags.flipy):
                    offsety = sprite_width - offsety
                if double:
                    offsetx >>= 1
                    offsety >>= 1
                spr_pal = self.sprites[index][offsetx][offsety]
                if spr_pal != 0:
                    col = self.palette[spr_pal]
                    if (flags & Sprite.Flags.main_screen):
                        log1 = (flags & Sprite.Flags.window_log1)
                        log2 = (flags & Sprite.Flags.window_log2)
                        if log1 and log2:
                            window = window_1 == window_2
                        elif log1 and not log2:
                            window = window_1 != window_2
                        elif not log1 and log2:
                            window = window_1 and window_2
                        elif not log1 and not log2:
                            window = window_1 or window_2
                        if (window and (flags & Sprite.Flags.in_window)) or (not window and (flags & Sprite.Flags.out_window)):
                            main = col
                            c_math = (flags & Sprite.Flags.c_math) > 0
                    if (flags & Sprite.Flags.sub_screen):
                        sub = col

        if not bg_handled:
            if not self.disable_backgound:
                bg0 = self.background[((y+self.bgscrollv)&511)*512+((x+self.bgscrollh)&511)]
                if bg0 != 0:
                    log1 = self.bg0_window_log1
                    log2 = self.bg0_window_log2
                    if log1 and log2:
                        window = window_1 == window_2
                    elif log1 and not log2:
                        window = window_1 != window_2
                    elif not log1 and log2:
                        window = window_1 and window_2
                    elif not log1 and not log2:
                        window = window_1 or window_2
                    if (window and self.bg0_in_window) or (not window and self.bg0_out_window):
                        main = bg0

        use_cmath = self.cmath_enable and c_math
        if use_cmath or self.fade_enable:
            main_r = (main >> 11) & 31
            main_g = (main >> 5) & 63
            main_b = (main >> 0) & 31
            if use_cmath:
                sub_r = (sub >> 11) & 31
                sub_g = (sub >> 5) & 63
                sub_b = (sub >> 0) & 31

                if self.double_main_screen:
                    main_r = (main_r << 1) & 31
                    main_g = (main_g << 1) & 63
                    main_b = (main_b << 1) & 31
                if self.half_main_screen:
                    main_r = (main_r >> 1)
                    main_g = (main_g >> 1)
                    main_b = (main_b >> 1)
                if self.double_sub_screen:
                    sub_r = (sub_r << 1) & 31
                    sub_g = (sub_g << 1) & 63
                    sub_b = (sub_b << 1) & 31
                if self.half_sub_screen:
                    sub_r = (sub_r >> 1)
                    sub_g = (sub_g >> 1)
                    sub_b = (sub_b >> 1)
                if self.add_sub_screen:
                    main_r = (main_r + sub_r) & 31
                    main_g = (main_g + sub_g) & 63
                    main_b = (main_b + sub_b) & 31
                if self.sub_sub_screen:
                    main_r = (main_r - sub_r) & 31
                    main_g = (main_g - sub_g) & 63
                    main_b = (main_b - sub_b) & 31
            if self.fade_enable:
                main_r = (main_r << 8) // self.screen_fade
                main_g = (main_g << 8) // self.screen_fade
                main_b = (main_b << 8) // self.screen_fade
            return (main_r << 11) | (main_g << 5) | (main_b)
        else:
            return main
                
    
    def render():
        # General steps:
        # Background is scrolled and blitted to the main screen
        # Solid colour is written to sub screen
        # Each sprite has a matrix applied, and they are written to the screen
        #  If the sprite is not enabled it is skipped
        #  If the sprite is flipped in the x or y it is applied after the matrix
        #  If the size bit is set the sprite is larger
        #  If the screen bit is set it is rendered to the sub screen instead of the main screen
        #  If color math is enabled or not is recorded in the color math enable buffer
        #  