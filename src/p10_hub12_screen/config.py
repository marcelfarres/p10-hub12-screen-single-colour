"""Panel metadata and lightweight pin configuration helpers."""

PANEL_INFO = {
    "model_family": "EEEEE EE908 style single-colour P10",
    "resolution": (32, 16),
    "interface": "HUB12",
    "scan_mode": "1/4 scan",
    "active_signals": ("CLK", "DR", "OE", "LAT", "A", "B"),
    "panel_c": "NC",
    "verified_board": "Freenove ESP32-S3 WROOM Lite FNK0099",
}

REQUIRED_PINS = ("clk", "dr", "oe", "lat", "a", "b")

FREENOVE_ESP32_S3_WROOM_PINS = {
    "clk": 16,
    "dr": 17,
    "oe": 18,
    "lat": 8,
    "a": 9,
    "b": 10,
}

# The Freenove ESP32-WROVER CAM board has an OV2640 camera physically wired
# to GPIOs 4, 5, 18, 19, 21, 22, 23, 25, 26, 27, 34-36, 39.
# Even when the camera is not used in software, those lines are loaded by
# camera circuitry (pull-ups, capacitors, OV2640 input impedance) and will
# corrupt fast-toggling HUB12 signals.  The pins below avoid all camera
# GPIOs, flash/PSRAM GPIOs (6-11, 16, 17), and risky strapping pins.
#   GPIO 15 — strapping pin but safe for output after boot.
#   GPIO  2 — built-in LED but fine for slow A/B row address.
FREENOVE_WROVER_PINS = {
    "clk": 13,
    "dr": 14,
    "oe": 32,
    "lat": 33,
    "a": 15,
    "b": 2,
}

PIN_PRESETS = {
    "freenove_s3_wroom": FREENOVE_ESP32_S3_WROOM_PINS,
    "freenove_wrover": FREENOVE_WROVER_PINS,
}

DEFAULT_OPTIONS = {
    "brightness": 0.5,
    "scan_period_ms": 3,
    "timer_id": 2,
    "use_spi": False,
}


class PinConfigurationError(ValueError):
    """Raised when the caller provides an invalid pin mapping."""


def validate_pins(pins, require_all=True):
    """Normalize and validate a pin mapping.

    Pin names are case-insensitive. Values must be integer-compatible GPIO ids.
    """
    if pins is None:
        if require_all:
            raise PinConfigurationError(
                "Pin mapping is required. Expected signals: %s."
                % ", ".join(name.upper() for name in REQUIRED_PINS)
            )
        return {}

    if not isinstance(pins, dict):
        raise PinConfigurationError("pins must be provided as a dict of signal -> GPIO")

    normalized = {}
    invalid_names = []
    for raw_name, raw_value in pins.items():
        name = str(raw_name).strip().lower()
        if name not in REQUIRED_PINS:
            invalid_names.append(str(raw_name))
            continue
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise PinConfigurationError(
                "GPIO for signal %s must be an integer-compatible value" % name.upper()
            ) from exc
        normalized[name] = value

    if invalid_names:
        raise PinConfigurationError(
            "Unsupported pin names: %s. Expected only: %s."
            % (
                ", ".join(invalid_names),
                ", ".join(name.upper() for name in REQUIRED_PINS),
            )
        )

    if require_all:
        missing = [name.upper() for name in REQUIRED_PINS if name not in normalized]
        if missing:
            raise PinConfigurationError(
                "Missing pin assignments for: %s." % ", ".join(missing)
            )

    return normalized


def get_pin_preset(name):
    """Return a validated pin mapping for a named preset."""
    preset_name = str(name).strip().lower()
    if preset_name not in PIN_PRESETS:
        raise PinConfigurationError(
            "Unsupported pin preset %r. Available presets: %s."
            % (name, ", ".join(sorted(PIN_PRESETS)))
        )
    return validate_pins(PIN_PRESETS[preset_name])


def resolve_pins(pins=None, pin_preset=None):
    """Return a full pin mapping from explicit pins or a named preset."""
    if pins is not None:
        if pin_preset is None:
            return validate_pins(pins)
        resolved = get_pin_preset(pin_preset)
        resolved.update(validate_pins(pins, require_all=False))
        return resolved

    if pin_preset is not None:
        return get_pin_preset(pin_preset)

    raise PinConfigurationError(
        "Provide pins={...} or pin_preset='name' when creating the screen."
    )


def format_pin_table(pins):
    """Return a compact display string for a validated pin mapping."""
    resolved = validate_pins(pins)
    return ", ".join("%s=%d" % (name.upper(), resolved[name]) for name in REQUIRED_PINS)
