"""MicroPython driver for the verified 32x16 single-colour P10 HUB12 panel."""

from machine import Pin, Timer
import time

try:
    import framebuf
except ImportError:
    framebuf = None


_TINY_FONT = {
    " ": ("000", "000", "000", "000", "000"),
    "!": ("010", "010", "010", "000", "010"),
    ".": ("000", "000", "000", "000", "010"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "001", "001", "001"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "A": ("111", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("111", "100", "100", "100", "111"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("111", "100", "101", "101", "111"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "P": ("111", "101", "111", "100", "100"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "Y": ("101", "101", "010", "010", "010"),
}


class P10Panel:
    """Driver for a single 32x16 P10 red LED panel via HUB12."""

    WIDTH = 32
    HEIGHT = 16
    _BPR = 4
    _GROUPS = 4
    _RPG = 4
    _BPS = 16

    def __init__(
        self,
        clk_pin,
        dr_pin,
        oe_pin,
        lat_pin,
        a_pin,
        b_pin,
        c_pin=None,
        brightness=0.5,
        use_spi=False,
        scan_period_ms=2,
        timer_id=2,
    ):
        if framebuf is None:
            self.enabled = False
            return

        self._clk = Pin(clk_pin, Pin.OUT, value=0)
        self._dr = Pin(dr_pin, Pin.OUT, value=0)
        self._clk_v = self._clk.value
        self._dr_v = self._dr.value

        self._spi = None
        if use_spi:
            try:
                from machine import SPI

                self._spi = SPI(
                    2,
                    baudrate=4_000_000,
                    polarity=0,
                    phase=0,
                    sck=Pin(clk_pin),
                    mosi=Pin(dr_pin),
                    miso=-1,
                )
            except Exception:
                self._clk = Pin(clk_pin, Pin.OUT, value=0)
                self._dr = Pin(dr_pin, Pin.OUT, value=0)
                self._clk_v = self._clk.value
                self._dr_v = self._dr.value

        self._lat = Pin(lat_pin, Pin.OUT, value=0)
        self._a = Pin(a_pin, Pin.OUT, value=0)
        self._b = Pin(b_pin, Pin.OUT, value=0)

        self._groups = self._GROUPS
        self._bps = self._BPS

        self._oe = Pin(oe_pin, Pin.OUT, value=1)
        self._brightness = max(0.0, min(1.0, float(brightness)))
        self._oe_enabled = self._brightness > 0.0

        self._buf = bytearray(self.WIDTH * self.HEIGHT // 8)
        self._fb = framebuf.FrameBuffer(
            self._buf, self.WIDTH, self.HEIGHT, framebuf.MONO_HLSB
        )
        self._scan_buf = bytearray(self._bps)
        self._scan_group = 0
        self._scan_period_ms = max(1, int(scan_period_ms))
        self._timer_id = int(timer_id)
        self.enabled = True

        self._fb.fill(0)
        self._timer = self._init_timer(self._timer_id)

    def _init_timer(self, preferred_timer_id):
        timer_ids = []
        for candidate in (preferred_timer_id, 1, 0):
            if candidate not in timer_ids:
                timer_ids.append(candidate)

        last_error = None
        for candidate in timer_ids:
            try:
                timer = Timer(candidate)
                timer.init(
                    period=self._scan_period_ms,
                    mode=Timer.PERIODIC,
                    callback=self._scan_isr,
                )
                self._timer_id = candidate
                return timer
            except Exception as exc:
                last_error = exc

        self.enabled = False
        raise RuntimeError("Unable to allocate a periodic timer") from last_error

    def _shift_out_sw(self, data):
        drv = self._dr_v
        clkv = self._clk_v
        for byte in data:
            drv(byte >> 7 & 1)
            clkv(1)
            clkv(0)
            drv(byte >> 6 & 1)
            clkv(1)
            clkv(0)
            drv(byte >> 5 & 1)
            clkv(1)
            clkv(0)
            drv(byte >> 4 & 1)
            clkv(1)
            clkv(0)
            drv(byte >> 3 & 1)
            clkv(1)
            clkv(0)
            drv(byte >> 2 & 1)
            clkv(1)
            clkv(0)
            drv(byte >> 1 & 1)
            clkv(1)
            clkv(0)
            drv(byte & 1)
            clkv(1)
            clkv(0)

    def _scan_isr(self, _timer):
        if not self.enabled:
            return

        oe = self._oe
        group = self._scan_group
        buf = self._buf
        sbuf = self._scan_buf
        idx = 0
        row_y = group

        # Match the original verified DMD scan layout exactly:
        # row+12, row+8, row+4, row+0 for each 8-pixel band.
        for band in range(self._BPR):
            sbuf[idx] = buf[(row_y + 12) * self._BPR + band] ^ 0xFF
            sbuf[idx + 1] = buf[(row_y + 8) * self._BPR + band] ^ 0xFF
            sbuf[idx + 2] = buf[(row_y + 4) * self._BPR + band] ^ 0xFF
            sbuf[idx + 3] = buf[(row_y + 0) * self._BPR + band] ^ 0xFF
            idx += 4

        if self._spi:
            self._spi.write(sbuf)
        else:
            self._shift_out_sw(sbuf)

        oe.value(0)
        self._lat.value(1)
        self._lat.value(0)
        self._a.value(group & 1)
        self._b.value((group >> 1) & 1)
        oe.value(1 if self._oe_enabled else 0)

        self._scan_group = (group + 1) % self._groups

    def _text(self, text, x=0, y=0):
        self._fb.text(text, x, y, 1)

    def _center(self, text, y=0):
        x = max(0, (self.WIDTH - len(text) * 8) // 2)
        self._fb.text(text, x, y, 1)

    def _tiny_text_width(self, text, spacing=1):
        text = (text or "").upper()
        if not text:
            return 0
        return len(text) * 3 + max(0, len(text) - 1) * spacing

    def _tiny_text(self, text, x=0, y=0, spacing=1):
        text = (text or "").upper()
        cursor_x = x
        for char in text:
            glyph = _TINY_FONT.get(char, _TINY_FONT[" "])
            for row, bits in enumerate(glyph):
                pixel_y = y + row
                if pixel_y < 0 or pixel_y >= self.HEIGHT:
                    continue
                for col, bit in enumerate(bits):
                    pixel_x = cursor_x + col
                    if bit == "1" and 0 <= pixel_x < self.WIDTH:
                        self._fb.pixel(pixel_x, pixel_y, 1)
            cursor_x += 3 + spacing

    def _center_tiny(self, text, y=0, spacing=1):
        x = max(0, (self.WIDTH - self._tiny_text_width(text, spacing)) // 2)
        self._tiny_text(text, x, y, spacing)

    def _fill_rect(self, x0, y0, width, height):
        x_start = max(0, int(x0))
        y_start = max(0, int(y0))
        x_end = min(self.WIDTH, int(x0 + width))
        y_end = min(self.HEIGHT, int(y0 + height))
        for x in range(x_start, x_end):
            for y in range(y_start, y_end):
                self._fb.pixel(x, y, 1)

    def _draw_hline(self, y_pos):
        if 0 <= y_pos < self.HEIGHT:
            for x in range(self.WIDTH):
                self._fb.pixel(x, y_pos, 1)

    def _sleep_ms(self, delay_ms):
        try:
            time.sleep_ms(int(delay_ms))
        except AttributeError:
            time.sleep(float(delay_ms) / 1000.0)

    def clear(self):
        self._fb.fill(0)

    def fill(self, value):
        self._fb.fill(1 if value else 0)

    def pixel(self, x, y, value=1):
        pixel_x = int(x)
        pixel_y = int(y)
        if 0 <= pixel_x < self.WIDTH and 0 <= pixel_y < self.HEIGHT:
            self._fb.pixel(pixel_x, pixel_y, 1 if value else 0)

    def fill_rect(self, x, y, width, height, value=1):
        x_start = max(0, int(x))
        y_start = max(0, int(y))
        x_end = min(self.WIDTH, int(x + width))
        y_end = min(self.HEIGHT, int(y + height))

        for pixel_x in range(x_start, x_end):
            for pixel_y in range(y_start, y_end):
                self._fb.pixel(pixel_x, pixel_y, 1 if value else 0)

    def show_text(self, text, x=0, y=0, clear=True):
        if clear:
            self._fb.fill(0)
        self._text(str(text).upper(), int(x), int(y))

    def show_centered_text(self, text, y=0, clear=True):
        if clear:
            self._fb.fill(0)
        self._center(str(text).upper(), int(y))

    def show_tiny_text(self, text, x=0, y=0, spacing=1, clear=True):
        if clear:
            self._fb.fill(0)
        self._tiny_text(str(text).upper(), int(x), int(y), int(spacing))

    def show_centered_tiny_text(self, text, y=0, spacing=1, clear=True):
        if clear:
            self._fb.fill(0)
        self._center_tiny(str(text).upper(), int(y), int(spacing))

    def show_two_lines(self, top, bottom, top_y=1, bottom_y=9, clear=True):
        if clear:
            self._fb.fill(0)
        self._center_tiny(str(top).upper(), int(top_y))
        bottom_text = str(bottom).upper()
        if len(bottom_text) <= 3:
            self._center(bottom_text, int(bottom_y) - 1)
        else:
            self._center_tiny(bottom_text, int(bottom_y))

    def show_debug_pattern(self, pattern="test"):
        pattern = (pattern or "test").lower()
        self._fb.fill(0)

        if pattern == "test":
            self._center("TEST", 0)
            for x in range(self.WIDTH):
                for y in range(8, self.HEIGHT):
                    if (x + y) & 1:
                        self._fb.pixel(x, y, 1)
            return

        if pattern == "all_on":
            self._fb.fill(1)
            return

        if pattern == "checker":
            for x in range(self.WIDTH):
                for y in range(self.HEIGHT):
                    if (x + y) & 1:
                        self._fb.pixel(x, y, 1)
            return

        if pattern == "top_half":
            self._fill_rect(0, 0, self.WIDTH, self.HEIGHT // 2)
            return

        if pattern == "bottom_half":
            self._fill_rect(0, self.HEIGHT // 2, self.WIDTH, self.HEIGHT // 2)
            return

        if pattern == "left_half":
            self._fill_rect(0, 0, self.WIDTH // 2, self.HEIGHT)
            return

        if pattern == "right_half":
            self._fill_rect(self.WIDTH // 2, 0, self.WIDTH // 2, self.HEIGHT)
            return

        if pattern == "frame":
            for x in range(self.WIDTH):
                self._fb.pixel(x, 0, 1)
                self._fb.pixel(x, self.HEIGHT - 1, 1)
            for y in range(self.HEIGHT):
                self._fb.pixel(0, y, 1)
                self._fb.pixel(self.WIDTH - 1, y, 1)
            return

        if pattern == "cross":
            for x in range(self.WIDTH):
                self._fb.pixel(x, self.HEIGHT // 2, 1)
            for y in range(self.HEIGHT):
                self._fb.pixel(self.WIDTH // 2, y, 1)
            return

        if pattern.startswith("band"):
            try:
                band_index = int(pattern[4:])
            except Exception:
                band_index = -1
            band_height = max(1, self.HEIGHT // 4)
            if 0 <= band_index < 4:
                self._fill_rect(0, band_index * band_height, self.WIDTH, band_height)
                return

        if pattern.startswith("row"):
            try:
                row_index = int(pattern[3:])
            except Exception:
                row_index = -1
            if 0 <= row_index < self.HEIGHT:
                self._draw_hline(row_index)
                return

        self._center("BAD", 0)
        self._center("PAT", 8)

    def set_brightness(self, brightness):
        self._brightness = max(0.0, min(1.0, float(brightness)))
        self._oe_enabled = self._brightness > 0.0

    def set_scan_period(self, scan_period_ms):
        self._scan_period_ms = max(1, int(scan_period_ms))
        self._timer.init(
            period=self._scan_period_ms,
            mode=Timer.PERIODIC,
            callback=self._scan_isr,
        )

    def deinit(self):
        self.enabled = False
        try:
            self._timer.deinit()
        except Exception:
            pass
        try:
            self._oe.value(1)
        except Exception:
            pass
        if self._spi:
            try:
                self._spi.deinit()
            except Exception:
                pass
