"""Standalone demo for the verified 32x16 HUB12 P10 panel."""

import time

from p10_hub12_screen import FREENOVE_WROVER_PINS, P10Screen


PANEL_PINS = FREENOVE_WROVER_PINS
HEART = (
    "01100110",
    "11111111",
    "11111111",
    "11111111",
    "01111110",
    "00111100",
    "00011000",
)


def sleep_ms(duration_ms):
    try:
        time.sleep_ms(duration_ms)
    except AttributeError:
        time.sleep(duration_ms / 1000.0)


def draw_bitmap(screen, bitmap, x=0, y=0):
    screen.clear()
    for row_index, row_bits in enumerate(bitmap):
        for col_index, bit in enumerate(row_bits):
            screen.pixel(x + col_index, y + row_index, bit == "1")


def main():
    screen = P10Screen(pins=PANEL_PINS)
    if not screen.enabled:
        return

    messages = ["HELLO", "P10", "READY"]
    patterns = ["test", "frame", "checker", "row0", "row15", "band0", "band3"]

    while True:
        for message in messages:
            screen.show_message(message)
            sleep_ms(1200)

        draw_bitmap(screen, HEART, x=12, y=4)
        sleep_ms(1200)

        for pattern in patterns:
            screen.show_debug_pattern(pattern)
            sleep_ms(800)

        screen.fill(1)
        sleep_ms(400)

        screen.clear()
        sleep_ms(400)


main()
