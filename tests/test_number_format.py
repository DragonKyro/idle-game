"""Unit tests for number formatting."""

from __future__ import annotations

import pytest

from src.number_format import format_duration, format_number, format_rate


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "0"),
        (1, "1"),
        (42, "42"),
        (999, "999"),
        (1000, "1.00K"),
        (1500, "1.50K"),
        (12_345, "12.3K"),
        (999_999, "1000K"),  # rounds up into next bucket's mantissa range
        (1_000_000, "1.00M"),
        (2_500_000, "2.50M"),
        (1_234_567_890, "1.23B"),
        (1e12, "1.00T"),
        (1e15, "1.00Qa"),
        (1e33, "1.00Dc"),
    ],
)
def test_format_number_positive(value, expected):
    assert format_number(value) == expected


def test_format_number_negative():
    assert format_number(-1500).startswith("-")


def test_format_number_very_large_falls_back_to_scientific():
    # Beyond Dc (1e33), we switch to scientific notation.
    result = format_number(1e40)
    assert "e" in result


def test_format_number_handles_none_gracefully():
    assert format_number(None) == "0"


def test_format_number_small_decimal():
    assert format_number(0.5) == "0.5"


def test_format_rate():
    assert format_rate(2.5) == "2.5/s"
    assert format_rate(1_500).endswith("/s")


@pytest.mark.parametrize(
    "seconds,expected_prefix",
    [
        (0, "0s"),
        (5, "5s"),
        (65, "1m"),
        (3725, "1h"),
    ],
)
def test_format_duration(seconds, expected_prefix):
    # Just check the prefix — the exact format is fine to evolve.
    assert format_duration(seconds).startswith(expected_prefix)
