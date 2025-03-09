#!/bin/bash
xtensa-esp32s3-elf-gcc -fPIC -shared -o main.s -O3 -S main.c -Wno-incompatible-pointer-types -Wno-int-conversion