# Prize Wheel Spinner (Pygame + ESP32)

A full-screen prize wheel for event booths, triggered by a physical ESP32 push button over USB serial.

<!-- TODO: add demo GIF/photo -->

## Overview

`Roulette.py` renders an 8-segment prize wheel in Pygame. A spin can be started from the keyboard or from an ESP32 that sends `s` over serial when its button is pressed. When the wheel lands on a prize, the PC sends `b` back to the ESP32, which sounds a buzzer.

The outcome is drawn from a weighted prize pool before the animation starts, then the wheel is eased (quartic ease-out) to stop on the matching segment. Prizes are removed from the pool once won, so each physical prize is given out only once.

## Features

- Resizable portrait window (540x960) with full-screen toggle and layout that scales to any resolution
- Weighted outcome: 6 winnable prizes against 63 "Zonk" (no prize) entries
- Non-repeating prizes: won items are removed from the pool
- Serial listener on a background thread, so the UI stays responsive
- Graceful fallback to keyboard-only mode if the serial port is not available
- ESP32 firmware with non-blocking button debounce and buzzer timer

## Hardware / Software

| Part | Details |
| --- | --- |
| PC app | Python 3, Pygame, pySerial |
| Controller | ESP32 (Arduino core) |
| Input | Push button on GPIO 12 (to GND, internal pull-up) |
| Output | Buzzer on GPIO 19 (6 s on a win) |
| Link | USB serial, 9600 baud, `/dev/ttyUSB0` by default |

## Serial protocol

| Direction | Byte | Meaning |
| --- | --- | --- |
| ESP32 to PC | `s` | Spin the wheel |
| PC to ESP32 | `b` | Prize won, sound the buzzer |

## Project structure

```
Roulette.py         Main Pygame application
asd.py              Variant of Roulette.py with "Motor" added to the winnable pool
assets/logo_ftek.png
button/button.ino   ESP32 firmware (button + buzzer)
```

## Getting started

1. Flash `button/button.ino` to the ESP32 with the Arduino IDE.
2. Install the Python dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Adjust `COM_PORT` in `Roulette.py` if the ESP32 is not on `/dev/ttyUSB0`.
4. Run:
   ```bash
   python Roulette.py
   ```

## Controls

| Key | Action |
| --- | --- |
| `Space` | Spin |
| `F` | Toggle full screen |
| `Esc` | Quit |

Prize names and odds are set in `visual_prizes` and `winnable_prizes_pool` in `Roulette.py`.
