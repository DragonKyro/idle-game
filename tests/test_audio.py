"""Unit tests for the audio synthesis — checks waveform shapes without
touching the audio device."""

from __future__ import annotations

import math

from src import audio


def test_every_recipe_produces_non_empty_samples():
    for name, recipe in audio._SOUND_RECIPES.items():
        samples = recipe()
        assert samples, f"{name} produced no samples"
        assert all(-1.0 <= s <= 1.0 for s in samples), (
            f"{name} has out-of-range samples"
        )


def test_note_frequencies_are_equal_temperament():
    # A4 is MIDI 69 = 440 Hz; C5 (MIDI 72) = 440 * 2^(3/12) ~= 523.25 Hz.
    assert math.isclose(audio._note(69), 440.0)
    assert math.isclose(audio._note(72), 523.251, rel_tol=1e-3)


def test_adsr_envelope_bounds():
    env = audio._adsr(0.1, 0.2, 0.5, 0.2)
    # Starts at 0, peaks at 1 during attack, sustains, fades to 0.
    assert math.isclose(env(0.0), 0.0, abs_tol=1e-6)
    assert math.isclose(env(0.1), 1.0, abs_tol=1e-6)       # end of attack
    assert math.isclose(env(0.3), 0.5, abs_tol=1e-6)       # end of decay
    assert math.isclose(env(0.5), 0.5, abs_tol=1e-6)       # sustain
    assert env(1.0) <= 1e-6                                # fully released


def test_click_is_short_and_bounded():
    click = audio._click()
    # Should be a short blip, well under 0.2s at 22kHz.
    assert 0 < len(click) < 22_050 * 0.2


def test_descend_is_about_one_second():
    descend = audio._descend()
    # Roughly 1s at 22kHz = ~22050 samples; tolerate small rounding.
    assert 21_000 <= len(descend) <= 23_000
