"""Human-friendly formatting for the very large numbers idle games produce."""

from __future__ import annotations

# Short-scale suffixes. After "Dc" we fall back to scientific notation to keep
# the shop cost labels readable.
_SUFFIXES = [
    "",    # 1
    "K",   # 1e3   thousand
    "M",   # 1e6   million
    "B",   # 1e9   billion
    "T",   # 1e12  trillion
    "Qa",  # 1e15  quadrillion
    "Qi",  # 1e18  quintillion
    "Sx",  # 1e21  sextillion
    "Sp",  # 1e24  septillion
    "Oc",  # 1e27  octillion
    "No",  # 1e30  nonillion
    "Dc",  # 1e33  decillion
]


def format_number(value: float) -> str:
    """Format `value` as a short, friendly string.

    Examples:
        0        -> "0"
        42       -> "42"
        1234     -> "1.23K"
        9_876_543 -> "9.88M"
        1e40     -> "1.00e40"
    """
    if value is None:
        return "0"

    # Preserve sign; the formatting logic below only deals with magnitudes.
    sign = "-" if value < 0 else ""
    value = abs(float(value))

    if value < 1000:
        # Integers shown as integers; small fractions get one decimal.
        if value == int(value):
            return f"{sign}{int(value)}"
        return f"{sign}{value:.1f}"

    # Pick the largest suffix that keeps the mantissa >= 1.
    import math

    exponent = int(math.floor(math.log10(value) / 3))
    if exponent >= len(_SUFFIXES):
        return f"{sign}{value:.2e}"

    mantissa = value / (1000 ** exponent)
    suffix = _SUFFIXES[exponent]
    # Two significant digits after the decimal feels right for shop prices.
    if mantissa >= 100:
        return f"{sign}{mantissa:.0f}{suffix}"
    if mantissa >= 10:
        return f"{sign}{mantissa:.1f}{suffix}"
    return f"{sign}{mantissa:.2f}{suffix}"


def format_rate(per_second: float) -> str:
    """Format a per-second production rate."""
    return f"{format_number(per_second)}/s"


def format_duration(seconds: float) -> str:
    """Compact duration: '3h 42m', '12m 05s', '47s'."""
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"
