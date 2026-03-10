"""Standalone package for the verified FlameSays P10 HUB12 panel."""

from .config import (
    DEFAULT_OPTIONS,
    FREENOVE_ESP32_S3_WROOM_PINS,
    FREENOVE_WROVER_PINS,
    PANEL_INFO,
    PinConfigurationError,
    PIN_PRESETS,
    REQUIRED_PINS,
    format_pin_table,
    get_pin_preset,
    resolve_pins,
    validate_pins,
)
from .panel import P10Panel
from .screen import P10Screen

__all__ = [
    "DEFAULT_OPTIONS",
    "FREENOVE_ESP32_S3_WROOM_PINS",
    "FREENOVE_WROVER_PINS",
    "PIN_PRESETS",
    "P10Panel",
    "P10Screen",
    "PANEL_INFO",
    "PinConfigurationError",
    "REQUIRED_PINS",
    "format_pin_table",
    "get_pin_preset",
    "resolve_pins",
    "validate_pins",
]
