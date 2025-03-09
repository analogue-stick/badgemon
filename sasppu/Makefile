# Location of top-level MicroPython directory
MPY_DIR = ../../badge-2024-software/micropython

# Name of module
MOD = sasppu

# Source files (.c or .py)
SRC = sasppu_fast.S sasppu_render.c sasppu_mpy.c

# Architecture to build for (x86, x64, armv6m, armv7m, xtensa, xtensawin)
ARCH = xtensawin

CFLAGS +=

# Include to get the rules for compiling and linking the module
include $(MPY_DIR)/py/dynruntime.mk

sasppu_fast.S: sasppu_gen.S

sasppu_gen.S: sasppu_generated.py
	python3 sasppu_generated.py

cleanall: clean
	$(RM) sasppu_gen.S

CROSS = xtensa-esp32s3-elf-

debug: all
	openocd -f board/esp32s3-builtin.cfg & xtensa-esp32s3-elf-gdb -x gdbinit path/to/micropython.elf