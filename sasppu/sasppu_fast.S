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

.set MAP_WIDTH_POWER (6)
.set MAP_HEIGHT_POWER (6)
.set MAP_WIDTH (1 << MAP_WIDTH_POWER)
.set MAP_HEIGHT (1 << MAP_HEIGHT_POWER)

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

  .section .bss
  .align 2
SASPPU.main_state.mainscreen_colour:
  .zero 1
SASPPU.main_state.subscreen_colour:
  .zero 1
SASPPU.main_state.window_1.left:
  .zero 1
SASPPU.main_state.window_1.right:
  .zero 1
SASPPU.main_state.window_2.left:
  .zero 1
SASPPU.main_state.window_2.right:
  .zero 1
SASPPU.main_state.flags:
  .zero 1
SASPPU.bg0_state:
  .zero size_of_Background
SASPPU.bg1_state:
  .zero size_of_Background
SASPPU.cmath_state.screen_fade:
  .zero 1
SASPPU.cmath_state.flags:
  .zero 1

SASPPU.oam:
  .zero (size_of_Sprite * SPRITE_COUNT)
SASPPU.bg0:
  .zero (MAP_WIDTH * MAP_HEIGHT * 2)
SASPPU.bg1:
  .zero (MAP_WIDTH * MAP_HEIGHT * 2)

// 256kb allocation
.align 16
SASPPU.background:
  .zero (BG_WIDTH * BG_HEIGHT * 2)
SASPPU.sprites:
  .zero (SPR_WIDTH * SPR_HEIGHT * 2)

// CONSTANTS
	.section	.rodata
	.align	16
	.type	vector_increments, @object
	.size	vector_increments, 16
vector_increments:
	.short	0
	.short	1
	.short	2
	.short	3
	.short	4
	.short	5
	.short	6
	.short	7

.text

.macro window_macro_q6 wincase
.if \wincase == 14
  ee.orq q5, q2, q3
  ee.notq q6, q6
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 13
  ee.andq q5, q2, q3
  ee.orq q6, q5, q6
  ee.notq q5, q6
.elseif \wincase == 12
  ee.xorq q5, q2, q3
  ee.notq q6, q6
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 11
  ee.notq q5, q3
  ee.notq q6, q6
  ee.orq q5, q2, q5
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 10
  ee.notq q6, q6
  ee.andq q5, q2, q6
  ee.notq q6, q5
.elseif \wincase == 9
  ee.orq q6, q3, q6
  ee.notq q5, q6
.elseif \wincase == 8
  ee.notq q5, q3
  ee.andq q5, q2, q5
  ee.notq q6, q6
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 7
  ee.notq q5, q2
  ee.orq q5, q3, q5
  ee.notq q6, q6
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 6
  ee.notq q6, q6
  ee.andq q5, q3, q6
  ee.notq q6, q5
.elseif \wincase == 5
  ee.orq q6, q2, q6
  ee.notq q5, q6
.elseif \wincase == 4
  ee.notq q5, q2
  ee.andq q5, q3, q5
  ee.notq q6, q6
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 3
  ee.xorq q5, q2, q3
  ee.orq q6, q5, q6
  ee.notq q5, q6
.elseif \wincase == 2
  ee.andq q5, q2, q3
  ee.notq q6, q6
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 1
  ee.orq q5, q2, q3
  ee.orq q6, q5, q6
  ee.notq q5, q6
.elseif \wincase == 15
  ee.notq q5, q6
.endif
.endm

.macro window_macro_q7 wincase
.if \wincase == 14
  ee.orq q5, q2, q3
  ee.notq q6, q7
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 13
  ee.andq q5, q2, q3
  ee.orq q6, q5, q7
  ee.notq q5, q6
.elseif \wincase == 12
  ee.xorq q5, q2, q3
  ee.notq q6, q7
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 11
  ee.notq q5, q3
  ee.orq q5, q2, q5
  ee.notq q6, q7
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 10
  ee.notq q6, q7
  ee.andq q5, q2, q6
  ee.notq q6, q5
.elseif \wincase == 9
  ee.orq q6, q3, q7
  ee.notq q5, q6
.elseif \wincase == 8
  ee.notq q5, q3
  ee.andq q5, q2, q5
  ee.notq q6, q7
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 7
  ee.notq q5, q2
  ee.orq q5, q3, q5
  ee.notq q6, q7
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 6
  ee.notq q6, q7
  ee.andq q5, q3, q6
  ee.notq q6, q5
.elseif \wincase == 5
  ee.orq q6, q2, q7
  ee.notq q5, q6
.elseif \wincase == 4
  ee.notq q5, q2
  ee.andq q5, q3, q5
  ee.notq q6, q7
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 3
  ee.xorq q5, q2, q3
  ee.orq q6, q5, q7
  ee.notq q5, q6
.elseif \wincase == 2
  ee.andq q5, q2, q3
  ee.notq q6, q7
  ee.andq q5, q5, q6
  ee.notq q6, q5
.elseif \wincase == 1
  ee.orq q5, q2, q3
  ee.orq q6, q5, q7
  ee.notq q5, q6
.elseif \wincase == 15
  mov.qr q6, q7
  ee.notq q5, q6
.endif
.endm

; both window settings are the same.
.macro window_macro_both wincase
.if \wincase == 0
.exitm
.endif

  ee.zero.q q6
  ee.vcmp.eq.s16 q6, q4, q6
  window_macro_q6 \wincase
  ee.andq q0, q0, q6
  ee.andq q1, q1, q6
  ee.andq q4, q4 ,q5
  ee.orq q0, q0, q4
  ee.orq q1, q1, q4
.endm

; just the main window
.macro window_macro_main wincase
.if \wincase == 0
.exitm
.endif

  window_macro_q7 \wincase
  ee.andq q0, q0, q6
  ee.andq q5, q4 ,q5
  ee.orq q0, q0, q5
.endm

; just the sub window
.macro window_macro_sub wincase
.if \wincase == 0
.exitm
.endif

  window_macro_q7 \wincase
  ee.andq q1, q1, q6
  ee.andq q5, q4 ,q5
  ee.orq q1, q1, q5
.endm

; Calculates the windows
.macro window_macro \mainwincase \subwincase
.if \mainwincase == \subwincase
  window_macro_both \mainwincase
.else

  ee.zero.q q7
  ee.vcmp.eq.s16 q7, q4, q7
  window_macro_main \mainwincase
  window_macro_sub \subwincase
.endif
.endm

// void handle_bg( //a0 return, a1 stack
  // uint8_t x, // a2
  // uint8_t y, // a3
  // SpriteCaches *sprite_caches, // a4
  // HandleBgType *handle_bg0, // a5
  // HandleBgType *handle_bg1, // a6
  // HandleCMathType *handle_cmath, // a7
  // vector_increments, // a8
  // struct Background *bg_state, // a9
  // BackgroundMap *bg_map, // a10
  //);
.macro handle_bg cmath_enable, main_screen_enable, sub_screen_enable, mainwincase subwincase
  
.endm


// void per_pixel( //a0 return, a1 stack
  // uint8_t x, // a2
  // uint8_t y, // a3
  // SpriteCaches *sprite_caches, // a4
  // HandleBgType *handle_bg0, // a5
  // HandleBgType *handle_bg1, // a6
  // HandleCMathType *handle_cmath, // a7
//);
	.literal_position
	.literal .LCvector_increments, vector_increments
	.literal .LCmainscreen_colour, SASPPU.main_state.mainscreen_colour
	.literal .LCsubscreen_colour, SASPPU.main_state.subscreen_colour
	.literal .LCwindow_1_left, SASPPU.main_state.window_1.left
	.literal .LCwindow_1_right, SASPPU.main_state.window_1.right
	.literal .LCwindow_2_left, SASPPU.main_state.window_2.left
	.literal .LCwindow_2_right, SASPPU.main_state.window_2.right
	.literal .LCbg0, SASPPU.bg0
	.literal .LCbg0_state, SASPPU.bg0_state
	.literal .LCbg1, SASPPU.bg1
	.literal .LCbg1_state, SASPPU.bg1_state
  .align 4
	.global per_pixel
  .type   per_pixel, @function
per_pixel:
  entry	sp, 80
	l32r	a8, .LCvector_increments
	l32r	a9, .LCmainscreen_colour
	l32r	a10, .LCsubscreen_colour
	l32r	a11, .LCwindow_1_left
	l32r	a12, .LCwindow_1_right
	l32r	a13, .LCwindow_2_left
	l32r	a14, .LCwindow_2_right

  ld.qr q0, a8, 0 // load increments
  ee.vldbc.16 q1, sp // broadcast x 
  ee.vadds.16 q0, q0, q1 // x_window
  ee.vldbc.16 q2, a11 // load window_1_left
  ee.vldbc.16 q3, a12 // load window_1_right
  ee.vcmp.eq.s16 q4, q0, q2
  ee.vcmp.gt.s16 q5, q0, q2
  ee.vcmp.eq.s16 q6, q0, q3
  ee.orq q4, q4, q5
  ee.vcmp.lt.s16 q5, q0, q3
  ee.vldbc.16 q3, a13 // load window_2_left
  ee.orq q5, q5, q6
  ee.vldbc.16 q7, a14 // load window_2_right
  ee.andq q2, q4, q5
  ee.vcmp.eq.s16 q4, q0, q3
  ee.vcmp.gt.s16 q5, q0, q3
  ee.vcmp.eq.s16 q6, q0, q7
  ee.orq q4, q4, q5
  ee.vcmp.lt.s16 q5, q0, q7
  ee.vcmp.lt.s16 q5, q0, q7
  ee.vldbc.16 q0, a9 // load main_col
  ee.orq q5, q5, q6
  ee.vldbc.16 q1, a10 // load sub_col
  ee.andq q3, q4, q5

	l32r	a9, .LCbg0_state
  l32r	a10, .LCbg0

  // handle bg0
	callx8	a5

  // handle bg1
	callx8	a6

  // handle cmath
	callx8	a8

	retw.n
	.size	per_pixel, .-per_pixel
