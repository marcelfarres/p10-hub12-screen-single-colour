"""High-level wrapper for rendering simple messages on a single HUB12 P10 panel."""

from .config import DEFAULT_OPTIONS, PANEL_INFO, format_pin_table, resolve_pins
from .panel import P10Panel


class P10Screen:
    """Convenience wrapper around P10Panel for common signage tasks."""

    MAX_TINY_LINE_CHARS = 8

    def __init__(
        self,
        pin_preset=None,
        pins=None,
        brightness=None,
        scan_period_ms=None,
        timer_id=None,
        use_spi=None,
    ):
        merged_pins = resolve_pins(pins=pins, pin_preset=pin_preset)

        options = DEFAULT_OPTIONS.copy()
        if brightness is not None:
            options["brightness"] = brightness
        if scan_period_ms is not None:
            options["scan_period_ms"] = scan_period_ms
        if timer_id is not None:
            options["timer_id"] = timer_id
        if use_spi is not None:
            options["use_spi"] = use_spi

        self.info = PANEL_INFO
        self.pin_preset = pin_preset
        self.pins = merged_pins
        self.pin_summary = format_pin_table(merged_pins)
        self.panel = P10Panel(
            clk_pin=merged_pins["clk"],
            dr_pin=merged_pins["dr"],
            oe_pin=merged_pins["oe"],
            lat_pin=merged_pins["lat"],
            a_pin=merged_pins["a"],
            b_pin=merged_pins["b"],
            brightness=options["brightness"],
            use_spi=options["use_spi"],
            scan_period_ms=options["scan_period_ms"],
            timer_id=options["timer_id"],
        )

    @property
    def enabled(self):
        return getattr(self.panel, "enabled", False)

    def _clean_text(self, value):
        return " ".join(str(value or "").upper().split())

    def _chunk_word(self, word):
        if len(word) <= self.MAX_TINY_LINE_CHARS:
            return [word]
        return [
            word[: self.MAX_TINY_LINE_CHARS],
            word[self.MAX_TINY_LINE_CHARS : self.MAX_TINY_LINE_CHARS * 2],
        ]

    def _fit_message_lines(self, message):
        if isinstance(message, (tuple, list)):
            top = self._clean_text(message[0] if len(message) > 0 else "")
            bottom = self._clean_text(message[1] if len(message) > 1 else "")
            return top[: self.MAX_TINY_LINE_CHARS], bottom[: self.MAX_TINY_LINE_CHARS]

        text = self._clean_text(message)
        if "\n" in str(message):
            parts = [
                self._clean_text(part) for part in str(message).splitlines() if part
            ]
            top = parts[0] if parts else ""
            bottom = parts[1] if len(parts) > 1 else ""
            return top[: self.MAX_TINY_LINE_CHARS], bottom[: self.MAX_TINY_LINE_CHARS]

        if len(text) <= self.MAX_TINY_LINE_CHARS:
            return text, ""

        words = text.split()
        if not words:
            return "", ""
        if len(words) == 1:
            chunks = self._chunk_word(words[0])
            if len(chunks) == 1:
                return chunks[0], ""
            return chunks[0], chunks[1]

        top_words = []
        bottom_words = []
        current = 0
        for word in words:
            target = top_words if not bottom_words else bottom_words
            tentative = (" ".join(target + [word])).strip()
            if len(tentative) <= self.MAX_TINY_LINE_CHARS:
                target.append(word)
                current = len(tentative)
                continue

            if not bottom_words:
                if top_words:
                    bottom_words.append(word)
                    current = len(word)
                else:
                    chunks = self._chunk_word(word)
                    top_words.append(chunks[0])
                    if len(chunks) > 1 and chunks[1]:
                        bottom_words.append(chunks[1])
                continue

            tentative_bottom = (" ".join(bottom_words + [word])).strip()
            if len(tentative_bottom) <= self.MAX_TINY_LINE_CHARS:
                bottom_words.append(word)
                current = len(tentative_bottom)
            else:
                break

        top = " ".join(top_words)[: self.MAX_TINY_LINE_CHARS]
        bottom = " ".join(bottom_words)[: self.MAX_TINY_LINE_CHARS]
        return top, bottom

    def clear(self):
        self.panel.clear()

    def fill(self, value=1):
        self.panel.fill(value)

    def pixel(self, x, y, value=1):
        self.panel.pixel(x, y, value)

    def fill_rect(self, x, y, width, height, value=1):
        self.panel.fill_rect(x, y, width, height, value)

    def show_text(self, text, x=0, y=0, clear=True):
        self.panel.show_text(self._clean_text(text), x=x, y=y, clear=clear)

    def show_lines(self, top, bottom):
        self.panel.show_two_lines(self._clean_text(top), self._clean_text(bottom))

    def show_message(self, message):
        top, bottom = self._fit_message_lines(message)
        if not top and not bottom:
            self.clear()
            return
        if bottom:
            self.panel.show_two_lines(top, bottom)
            return
        if len(top) <= 3:
            self.panel.show_centered_text(top, 4)
        else:
            self.panel.show_centered_tiny_text(top, 5)

    def show_number(self, value, label=""):
        value_text = self._clean_text(value)
        label_text = self._clean_text(label)
        if label_text:
            self.panel.show_two_lines(
                label_text[: self.MAX_TINY_LINE_CHARS], value_text
            )
            return
        if len(value_text) <= 3:
            self.panel.show_centered_text(value_text, 4)
        else:
            self.panel.show_centered_tiny_text(value_text, 5)

    def show_debug_pattern(self, name="test"):
        self.panel.show_debug_pattern(name)

    def set_brightness(self, value):
        self.panel.set_brightness(value)

    def deinit(self):
        self.panel.deinit()
