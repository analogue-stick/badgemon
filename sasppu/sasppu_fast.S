//
// ESP32-S3 ASM SIMD code
// Part of SASPPU
// Written by Molive
//
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

PSEUDOCODE:

.bss
  WINDOW_STATE_0: .res 16
  WINDOW_STATE_1: .res 16
  WINDOW_STATE_2: .res 16
  WINDOW_STATE_3: .res 16

// Q0: x A3: y Q1: main_col Q2: sub_col Q3: c_math
// Ruins all other Q registers.
handle_bg0:
#if enable_bg0 && ((bg0_main_screen_enable && (bg0_main_in_window || bg0_main_out_window)) || (bg0_sub_screen_enable && (bg0_sub_in_window || bg0_sub_out_window)))
  q4 = (((a3+bg0scrollv)&0x01FF << 9) + (x+bg0scrollh)) & 0xFFF0
  q5 = (((a3+bg0scrollv)&0x01FF << 9) + (x+bg0scrollh) + 16) & 0xFFF0
  q4 = (q4 ++ q5) << // perform the weird unaligned access thing
  q5 = 0
  q5 = q4 == q5 // q5 = bg0 == 0
  q5 = ~q5 // bg0 != 0

#if bg0_main_screen_enable && (bg0_main_in_window || bg0_main_out_window)
#if bg0_main_in_window && bg0_main_out_window
  q6 = q5
#else
  q6 = WINDOW_STATE[bg0_main_window_log]
#if bg0_main_out_window
  q6 = ~q6
#endif
#endif
  // q6 = get_window(..)
  q6 = q6 & q5 // q6 = bg0 != 0 && bg0_main_screen_enable && get_window(..)
  q7 = q4 & q6
  q6 = ~q6
  q1 = q1 & q6
  q1 = q1 | q7 // select statement. Takes four commands :/
  q3 = q3 & q6
  q6 = ~q6
  q7 = bg0_cmath_enable // broadcast
  q7 = q7 & q6
  q3 = q3 | q7 // Set c_math also
#endif

#if bg0_sub_screen_enable && (bg0_sub_in_window || bg0_sub_out_window)
#if bg0_sub_in_window && bg0_sub_out_window
  q6 = q5
#else
  q6 = WINDOW_STATE[bg0_sub_window_log]
#if bg0_sub_out_window
  q6 = ~q6
#endif
#endif
  // q6 = get_window(..)
  q6 = q6 & q5 // q6 = bg0 != 0 && bg0_sub_screen_enable && get_window(..)
  q7 = q4 & q6
  q6 = ~q6
  q2 = q2 & q6
  q2 = q2 | q7 // select statement. Takes four commands :/
#endif
#endif
  retw.n

// A2: x A3: y
per_8pixels:
  q0 = x positions
  q1 = mainscreen_colour // main_col, broadcast
  q2 = subscreen_colour // sub_col, broadcast
  q3 = false // c_math, broadcast

  q4 = (q0 >= window_1_left) && (q0 <= window_1_right)
  q5 = (q0 >= window_2_left) && (q0 <= window_2_right)
  q6 = q4 | q5
  WINDOW_STATE_0 = q6
  q6 = q4 & q5
  WINDOW_STATE_1 = q6
  q6 = q4 ^ q5
  WINDOW_STATE_2 = q6
  q6 = ~q6
  WINDOW_STATE_3 = q6
  
  handle_bg0()

  a1 = 16
high_sprite_loop:
  a1 -= 1
  bne high_sprite_loop