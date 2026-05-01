"""Procedural chiptune audio.

We synthesize every sound effect as a WAV at startup (cached to
``assets/sounds/``) and wrap them as ``arcade.Sound``. No binary audio
assets are shipped with the repo.

Tone palette is intentionally simple — sine/triangle/square waves plus
ADSR envelopes and small chord stacks — which reads as "retro arcade"
and fits the pixel-art crystal theme. Real production would replace
these with commissioned SFX, but they sound coherent out of the box.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path
from typing import Callable, Iterable

import arcade


_SAMPLE_RATE = 22_050
_SOUND_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"


# ----------------------------------------------------------------------
# Waveform primitives.
# ----------------------------------------------------------------------

def _sine(freq: float, t: float) -> float:
    return math.sin(2 * math.pi * freq * t)


def _triangle(freq: float, t: float) -> float:
    phase = (t * freq) % 1.0
    return 4 * abs(phase - 0.5) - 1


def _square(freq: float, t: float) -> float:
    return 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0


def _noise(_freq: float, _t: float) -> float:
    return random.uniform(-1.0, 1.0)


_WAVES = {"sine": _sine, "tri": _triangle, "square": _square, "noise": _noise}


def _adsr(attack: float, decay: float, sustain: float, release: float) -> Callable[[float], float]:
    """Amplitude envelope — inputs are 0..1 normalized progress."""
    def env(t: float) -> float:
        if t < attack:
            return t / attack if attack > 0 else 1.0
        if t < attack + decay:
            return 1.0 - (t - attack) / decay * (1.0 - sustain) if decay > 0 else sustain
        if t < 1.0 - release:
            return sustain
        return sustain * max(0.0, 1.0 - (t - (1.0 - release)) / release) if release > 0 else 0.0
    return env


def _synth(
    *,
    freq: float,
    duration: float,
    wave_type: str = "sine",
    envelope: Callable[[float], float] | None = None,
    pitch_glide: tuple[float, float] | None = None,
) -> list[float]:
    """Render a single tone into a list of float samples in [-1, 1]."""
    w = _WAVES[wave_type]
    n = int(duration * _SAMPLE_RATE)
    samples: list[float] = []
    for i in range(n):
        t = i / _SAMPLE_RATE
        norm = i / max(1, n - 1)
        if pitch_glide is not None:
            start, end = pitch_glide
            current_freq = start + (end - start) * norm
        else:
            current_freq = freq
        v = w(current_freq, t)
        if envelope is not None:
            v *= envelope(norm)
        samples.append(v)
    return samples


def _mix(tracks: Iterable[list[float]]) -> list[float]:
    """Additively mix equal-length (or zero-padded) sample lists."""
    materialized = [list(t) for t in tracks]
    if not materialized:
        return []
    length = max(len(t) for t in materialized)
    out = [0.0] * length
    for t in materialized:
        for i, v in enumerate(t):
            out[i] += v
    # Soft-clip so we don't wrap.
    return [max(-1.0, min(1.0, v)) for v in out]


def _concat(tracks: Iterable[list[float]]) -> list[float]:
    out: list[float] = []
    for t in tracks:
        out.extend(t)
    return out


def _save_wav(samples: list[float], path: Path, peak: float = 0.6) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(_SAMPLE_RATE)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * peak * 32767))
            for s in samples
        )
        wf.writeframes(frames)


# ----------------------------------------------------------------------
# Sound recipes — short, chunky, and readable.
# ----------------------------------------------------------------------

# Equal-temperament frequency for MIDI notes. A4 = 69 = 440 Hz.
def _note(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12))


def _click() -> list[float]:
    # Sharp high blip — ~900 Hz, quick decay.
    env = _adsr(0.002, 0.02, 0.1, 0.03)
    return _synth(freq=900, duration=0.06, wave_type="tri", envelope=env)


def _purchase() -> list[float]:
    # Two-note rising arpeggio (C5 → E5).
    env = _adsr(0.005, 0.04, 0.3, 0.08)
    a = _synth(freq=_note(72), duration=0.09, wave_type="tri", envelope=env)
    b = _synth(freq=_note(76), duration=0.12, wave_type="tri", envelope=env)
    return _concat([a, b])


def _level_up() -> list[float]:
    # Three rising notes (C5, E5, G5) with a tiny triangle sparkle layered.
    env = _adsr(0.005, 0.05, 0.35, 0.1)
    notes = [
        _synth(freq=_note(72), duration=0.1, wave_type="tri", envelope=env),
        _synth(freq=_note(76), duration=0.1, wave_type="tri", envelope=env),
        _synth(freq=_note(79), duration=0.16, wave_type="tri", envelope=env),
    ]
    return _concat(notes)


def _max_level() -> list[float]:
    # Triumphant four-note flourish with a chord on the last note.
    env = _adsr(0.005, 0.05, 0.4, 0.12)
    chord_env = _adsr(0.005, 0.1, 0.5, 0.25)
    seq = [
        _synth(freq=_note(72), duration=0.09, wave_type="tri", envelope=env),
        _synth(freq=_note(76), duration=0.09, wave_type="tri", envelope=env),
        _synth(freq=_note(79), duration=0.09, wave_type="tri", envelope=env),
    ]
    # Chord: C5+E5+G5+C6 stacked for the final note.
    chord = _mix([
        _synth(freq=_note(72), duration=0.4, wave_type="tri", envelope=chord_env),
        _synth(freq=_note(76), duration=0.4, wave_type="tri", envelope=chord_env),
        _synth(freq=_note(79), duration=0.4, wave_type="tri", envelope=chord_env),
        _synth(freq=_note(84), duration=0.4, wave_type="tri", envelope=chord_env),
    ])
    return _concat(seq + [chord])


def _descend() -> list[float]:
    # Low descending glide (A3 → A2) + a high sparkle chime.
    glide_env = _adsr(0.01, 0.1, 0.45, 0.4)
    glide = _synth(
        freq=0, duration=1.0, wave_type="sine",
        envelope=glide_env, pitch_glide=(_note(57), _note(45)),
    )
    sparkle_env = _adsr(0.005, 0.08, 0.2, 0.2)
    # Pause + bell
    silence = [0.0] * int(0.3 * _SAMPLE_RATE)
    sparkle = _mix([
        _synth(freq=_note(84), duration=0.5, wave_type="sine", envelope=sparkle_env),
        _synth(freq=_note(88), duration=0.5, wave_type="sine", envelope=sparkle_env),
    ])
    # Overlay sparkle over the tail of the glide (mix after concatenation).
    front = glide
    tail = _concat([silence, sparkle])
    length = max(len(front), len(tail))
    front += [0.0] * (length - len(front))
    tail += [0.0] * (length - len(tail))
    # Soft-clip so the summed waveforms never escape [-1, 1].
    return [max(-1.0, min(1.0, a + b)) for a, b in zip(front, tail)]


def _event_chime() -> list[float]:
    # Light sparkle for golden-shard / lucky-critter spawns.
    env = _adsr(0.005, 0.05, 0.2, 0.15)
    return _mix([
        _synth(freq=_note(84), duration=0.3, wave_type="sine", envelope=env),
        _synth(freq=_note(91), duration=0.3, wave_type="sine", envelope=env),
    ])


def _boss_hit() -> list[float]:
    # Meaty thump — low square + short noise burst.
    env = _adsr(0.003, 0.04, 0.0, 0.05)
    thump = _synth(freq=_note(38), duration=0.12, wave_type="square", envelope=env)
    noise_env = _adsr(0.001, 0.02, 0.0, 0.04)
    hit = _synth(freq=0, duration=0.08, wave_type="noise", envelope=noise_env)
    return _mix([thump, hit + [0.0] * (len(thump) - len(hit))])


def _boss_defeat() -> list[float]:
    # Ascending chord with a cymbal-y noise tail.
    env = _adsr(0.005, 0.08, 0.35, 0.25)
    chord = _mix([
        _synth(freq=_note(60), duration=0.6, wave_type="tri", envelope=env),
        _synth(freq=_note(64), duration=0.6, wave_type="tri", envelope=env),
        _synth(freq=_note(67), duration=0.6, wave_type="tri", envelope=env),
        _synth(freq=_note(72), duration=0.6, wave_type="tri", envelope=env),
    ])
    noise_env = _adsr(0.01, 0.05, 0.15, 0.3)
    sparkle = _synth(freq=0, duration=0.6, wave_type="noise", envelope=noise_env)
    sparkle = [v * 0.3 for v in sparkle]
    return _mix([chord, sparkle])


_SOUND_RECIPES: dict[str, Callable[[], list[float]]] = {
    "click": _click,
    "purchase": _purchase,
    "level_up": _level_up,
    "max_level": _max_level,
    "descend": _descend,
    "event": _event_chime,
    "boss_hit": _boss_hit,
    "boss_defeat": _boss_defeat,
}


# ----------------------------------------------------------------------
# Public facade — build once, play many.
# ----------------------------------------------------------------------

class AudioLibrary:
    """Lazy-initialized library of named sounds.

    Synthesizes WAVs on first construction (or if the cache file is
    missing) and loads them as ``arcade.Sound``. All playback goes
    through ``play(name, category)`` so volume is centrally controlled.
    """

    def __init__(self) -> None:
        self._sounds: dict[str, arcade.Sound] = {}
        self._sfx_volume: float = 0.6
        # Space reserved for future ambient bed.
        self._music_volume: float = 0.4
        self._muted: bool = False

        for name, recipe in _SOUND_RECIPES.items():
            path = _SOUND_DIR / f"{name}.wav"
            if not path.exists():
                samples = recipe()
                _save_wav(samples, path)
            try:
                self._sounds[name] = arcade.Sound(path)
            except Exception:
                # Playback is optional — keep the rest of the game usable.
                pass

    # -- settings interface ----------------------------------------------

    @property
    def sfx_volume(self) -> float:
        return self._sfx_volume

    @sfx_volume.setter
    def sfx_volume(self, value: float) -> None:
        self._sfx_volume = max(0.0, min(1.0, value))

    @property
    def music_volume(self) -> float:
        return self._music_volume

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        self._music_volume = max(0.0, min(1.0, value))

    @property
    def muted(self) -> bool:
        return self._muted

    @muted.setter
    def muted(self, value: bool) -> None:
        self._muted = bool(value)

    # -- playback ---------------------------------------------------------

    def play(self, name: str, *, gain: float = 1.0) -> None:
        """Play a SFX by name. ``gain`` is a per-event scale on top of
        the global SFX volume."""
        if self._muted:
            return
        sound = self._sounds.get(name)
        if sound is None:
            return
        volume = max(0.0, min(1.0, self._sfx_volume * gain))
        if volume <= 0.0:
            return
        try:
            sound.play(volume=volume)
        except Exception:
            # Arcade / pyglet sometimes raises if the audio device is busy;
            # swallowing keeps gameplay smooth.
            pass
