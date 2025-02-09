//
// ESP32-S3 ASM SIMD code
// Part of SASPPU
// Written by Molive
//

// Sprite
// size = 10, align = 2
  .struct 0
Sprite:
  .space 0
Sprite.x:
  .space 2
Sprite.y:
  .space 2
Sprite.width:
  .space 1
Sprite.height:
  .space 1
Sprite.graphics.x:
  .space 1
Sprite.graphics.y:
  .space 1
Sprite.flags:
  .space 2
size_of_Sprite:

// size = 6, align = 2
  .struct 0
Background:
  .space 0
Background.scroll.x:
  .space 2
Background.scroll.y:
  .space 2
Background.windows:
  .space 1
Background.flags:
  .space 1
size_of_Background:

// size = 2, align = 1
  .struct 0
ColorMath:
  .space 0
ColorMath.screen_fade:
  .space 1
ColorMath.flags:
  .space 1
size_of_ColorMath

// size = 10, align = 2
  .struct 0
State:
  .space 0
State.mainscreen_colour:
  .space 2
State.subscreen_colour:
  .space 2
State.window_1.left:
  .space 1
State.window_1.right:
  .space 1
State.window_2.left:
  .space 1
State.window_2.right:
  .space 1
State.flags:
  .space 1
size_of_State:

.set BG_WIDTH_POWER (8)
.set BG_HEIGHT_POWER (8)
.set BG_WIDTH (1 << BG_WIDTH_POWER)
.set BG_HEIGHT (1 << BG_HEIGHT_POWER)

.set SPRITE_COUNT (256)
.set SPRITE_CACHE (16)

.set SPR_WIDTH_POWER (8)
.set SPR_HEIGHT_POWER (8)
.set SPR_WIDTH (1 << SPR_WIDTH_POWER)
.set SPR_HEIGHT (1 << SPR_HEIGHT_POWER)

.set SPR_ENABLED (1 << 0)
.set SPR_PRIORITY (1 << 1)
.set SPR_FLIP_X (1 << 2)
.set SPR_FLIP_Y (1 << 3)
.set SPR_MAIN_SCREEN (1 << 4)
.set SPR_SUB_SCREEN (1 << 5)
.set SPR_C_MATH (1 << 6)
.set SPR_DOUBLE (1 << 7)
.set SPR_MAIN_WINDOW_POW2 (8)
.set SPR_MAIN_WINDOW_LOG1 (1 << 8)
.set SPR_MAIN_WINDOW_LOG2 (1 << 9)
.set SPR_MAIN_WINDOW_LOG3 (1 << 1)
.set SPR_MAIN_WINDOW_LOG4 (1 << 1)
.set SPR_SUB_WINDOW_POW2 (12)
.set SPR_SUB_WINDOW_LOG1 (1 << 12)
.set SPR_SUB_WINDOW_LOG2 (1 << 13)
.set SPR_SUB_WINDOW_LOG3 (1 << 14)
.set SPR_SUB_WINDOW_LOG4 (1 << 15)

.set WINDOW_A (0b0001)
.set WINDOW_B (0b0010)
.set WINDOW_AB (0b0100)
.set WINDOW_X (0b1000)

  .bss
  .align 2
SASPPU.main_state:
  .zero size_of_State
SASPPU.bg0_state:
  .zero size_of_Background
SASPPU.bg1_state:
  .zero size_of_Background
SASPPU.cmath_state:
  .zero size_of_ColorMath
SASPPU.oam:
  .zero (size_of_Sprite * SPRITE_COUNT)

.align 16
// 128kb
SASPPU.bg0:
  .zero (BG_WIDTH * BG_HEIGHT) 
SASPPU.bg1:
  .zero (BG_WIDTH * BG_HEIGHT)
SASPPU.sprites:
  .zero (SPR_WIDTH * SPR_HEIGHT)


	.text
	.align 4

// Simple signed 16-bit x 8 add
// registers with the args:     A2            A3            A4
// Call as int s3_add16x8(int16_t *pA, int16_t *pB, int16_t *pC);
	.global s3_add16x8
  .type   s3_add16x8,@function
s3_add16x8:
  entry   a1,16            # prepare windowed registers and reserve 16 bytes of stack
  ee.vld.128.ip	q0,a2,16   # load 8 "A" values into Q0 from A2, then add 16 to A2
  ee.vld.128.ip	q1,a3,16   # load 8 "B" values into Q1 from A3, then add 16 to A3
  ee.vadds.s16 q2,q0,q1    # C = A+B (with saturation)
  ee.vst.128.ip q2,a4,16   # store the 8 "C" values, then add 16 to A4
	movi.n	a2,0             # return value of 0
	retw.n                   # restore state (windowed registers) and return to caller
