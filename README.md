# p10-hub12-screen

Small MicroPython package for a single-colour 32x16 HUB12 P10 panel.

## Quick Start

Copy `src/p10_hub12_screen` into your device `lib` directory, then use:

```python
from p10_hub12_screen import FREENOVE_ESP32_S3_WROOM_PINS, P10Screen

screen = P10Screen(pins=FREENOVE_ESP32_S3_WROOM_PINS)
screen.show_text("HI", x=0, y=0)
screen.pixel(12, 8, 1)
screen.fill_rect(14, 8, 3, 3, 1)
```

Or use a preset name:

```python
screen = P10Screen(pin_preset="freenove_s3_wroom")
```

## Board Presets

### Freenove ESP32-S3 WROOM (verified)

```python
FREENOVE_ESP32_S3_WROOM_PINS = {
    "clk": 16, "dr": 17, "oe": 18, "lat": 8, "a": 9, "b": 10,
}
```

Preset name: `freenove_s3_wroom`

### Freenove ESP32-WROVER CAM (verified)

```python
FREENOVE_WROVER_PINS = {
    "clk": 13, "dr": 14, "oe": 32, "lat": 33, "a": 15, "b": 2,
}
```

Preset name: `freenove_wrover`

## Warning: Boards with Camera Modules

Many ESP32 development boards include a camera (e.g. OV2640) that is
**physically wired** to a large number of GPIOs. Even when no camera software
is running, the camera circuitry (pull-ups, capacitors, sensor input impedance)
loads those GPIO lines and will corrupt fast-toggling signals like HUB12 CLK,
OE, and LAT.

**Always check the schematic of your board before choosing pins.** Avoid any
GPIO that is connected to the camera, flash, or PSRAM.

The Freenove ESP32-WROVER CAM board, for example, uses GPIOs 4, 5, 18, 19,
21, 22, 23, 25, 26, 27, 34-36, 39 for its camera. The preset above uses only
camera-free GPIOs.

## Pin Names

The six HUB12 signals: `clk`, `dr`, `oe`, `lat`, `a`, `b`.

## API

- `P10Screen(pins=..., pin_preset=...)` — create screen
- `clear()` / `fill(value)` — blank or fill
- `pixel(x, y, value=1)` — set pixel
- `fill_rect(x, y, w, h, value=1)` — rectangle
- `show_text(text, x=0, y=0)` — 8x8 font text
- `show_message(message)` — auto-layout text
- `show_debug_pattern(name)` — wiring test patterns
- `set_brightness(value)` / `deinit()`

Debug patterns: `test`, `checker`, `frame`, `row0`, `row15`, `band0`-`band3`,
`all_on`, `top_half`, `bottom_half`, `left_half`, `right_half`, `cross`.

## Deploy

```bash
uv run python deploy_to_esp32.py --device COM10
```

## Notes

- Verified on Freenove ESP32-S3 WROOM Lite FNK0099 and Freenove ESP32-WROVER CAM.
- Other ESP32 boards should work if they expose six free output GPIOs and
  support `machine.Timer` + `framebuf` in MicroPython.
