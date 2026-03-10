from p10_hub12_screen import FREENOVE_ESP32_S3_WROOM_PINS, P10Screen


HEART = (
    "01100110",
    "11111111",
    "11111111",
    "11111111",
    "01111110",
    "00111100",
    "00011000",
)


def draw_bitmap(screen, bitmap, x=0, y=0):
    for row_index, row_bits in enumerate(bitmap):
        for col_index, bit in enumerate(row_bits):
            screen.pixel(x + col_index, y + row_index, bit == "1")


screen = P10Screen(pins=FREENOVE_ESP32_S3_WROOM_PINS)
screen.clear()
screen.show_text("HI", x=0, y=0)
draw_bitmap(screen, HEART, x=12, y=4)
