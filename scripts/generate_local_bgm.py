#!/usr/bin/env python3
"""Generate a deterministic, low-key instrumental WAV for the default BGM layer."""
from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mood", choices=("calm", "warm", "focused", "uplifting"), required=True)
    args = parser.parse_args()
    if args.duration <= 0:
        raise SystemExit("duration must be positive")
    sample_rate = 48000
    frames = int(args.duration * sample_rate)
    notes_by_mood = {
        "calm": ((196.0, 0.18), (246.94, 0.12), (293.66, 0.10), (392.0, 0.06)),
        "warm": ((174.61, 0.18), (220.0, 0.12), (261.63, 0.10), (329.63, 0.06)),
        "focused": ((220.0, 0.18), (277.18, 0.12), (329.63, 0.10), (440.0, 0.06)),
        "uplifting": ((220.0, 0.18), (293.66, 0.12), (349.23, 0.10), (523.25, 0.06)),
    }
    notes = notes_by_mood[args.mood]
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(frames):
            t = i / sample_rate
            cycle = t % 8.0
            fade_in = min(1.0, t / 1.0)
            fade_out = min(1.0, max(0.0, (args.duration - t) / 1.5))
            level = 0.12 * fade_in * fade_out
            tone = sum(math.sin(2 * math.pi * freq * t) * amp for freq, amp in notes)
            pulse = 0.88 + 0.12 * math.sin(2 * math.pi * cycle / 8.0)
            value = max(-1.0, min(1.0, tone * level * pulse))
            sample = int(value * 32767)
            wav.writeframesraw(struct.pack('<hh', sample, sample))
    print(f"Local BGM created ({args.mood}): {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
