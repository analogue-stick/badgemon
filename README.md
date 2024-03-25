# Project Description

A Pokemon style video game designed to be played on the EMF Camp badges. The core principal involves being able to challenge other badge holders to a battle using two devices over Bluetooth.

The game must be written and designed for the EMF 2024 badges, which come equipped with a ESP32-S3 running a standard build of micropython. Peripherals include:

- One 240p round screen, to be used as the main game display
- Six buttons around the corners of the hexagon
- Motion sensor
- Bluetooth/WiFi
- "Many, many LED’s"

(further information can be found at [emfcamp/badge-2024-hardware](https://github.com/emfcamp/badge-2024-hardware) on Github)


Additional scope for expansion:

- Location-based random encounters (similar to Pokemon Go)

# Project Breakdown

This project is quite large in scope, especially since this is being written from the ground up.

## Game Design
- Designing the core gameplay loop
- Monsters and their movesets
- Playtesting/tweaking balance issues

## Art and Graphics
- UI design
- Sprite work

## Implementation
- Implementing the core game logic
- UI implementation
- IO handling
- Wireless communications (BLE)

# Additional notes

While a lot of this work can be done without, a lack of access to the physical device will hinder progress, specifically to the implementation section of the breakdown. However if the game is written in micropython then a lot of this can be prototyped on any device running it with BLE capabilities, like a PicoW (£6.30), since the standard functionality is cross platform.

Performance-wise it is worth noting the limitations of micropython. It is not a fast language, and would be valuable to be familiar with the [documentation](https://docs.micropython.org/en/latest/reference/speed_python.html) on writing performant micropython.

In terms of designing monsters it would be worthwhile exercising restraint, this is a two month project worked on in free time only. This will require at least one sprite per monster, possibly two if the traditional pokemon battle screen is to be mimicked. 

# Initial Steps

I would suggest starting by creating a prototype of the game for PC in python. This will create enough of a foundation to start working on implementation and the game design.

## creaturedoc
https://docs.google.com/spreadsheets/d/1bPqPAizbvCg3qRgEczM2HZmXpHMe7Wuyh-J5jB7HzRk/edit?usp=sharing