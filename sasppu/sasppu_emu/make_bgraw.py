#!/bin/python
import os
from PIL import Image

for f in os.listdir("./assets/"):
    if f.endswith(".png"):
        new_pixels = []
        with Image.open("assets/"+f) as im:
            pixels = list(im.convert("RGBA").getdata())
            for pixel in pixels:
                if pixel[3] < 255:
                    new_pixel = (0,0,0)
                else:
                    new_pixel = (pixel[0] >> 3, pixel[1] >> 3, pixel[2] >> 3)
                    if new_pixel == (0,0,0):
                        new_pixel = (0,0,1)
                new_pixels.append((new_pixel[0] << 10 | new_pixel[1] << 5 | new_pixel[2]).to_bytes(2, "little"))
        with open("assets/"+f+".bgraw", "wb") as im:
            for pixel in new_pixels:
                im.write(pixel)