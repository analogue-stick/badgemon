#!/bin/bash
xtensa-esp32s3-elf-gcc -fPIC -shared -o main.s -S -O3 main.c