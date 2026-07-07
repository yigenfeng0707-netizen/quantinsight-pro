#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate TTS narration MP3s for Remotion demo video."""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    edge_tts = None

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "demo-video-remotion" / "public" / "audio"
STORYBOARD = ROOT / "demo.storyboard.json"
VOICE = "zh-CN-YunxiNeural"
RATE = "-8%"


async def synth(text: str, out: Path) -> None:
    text = text.replace("——", "，")
    if edge_tts:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(out))
                if out.stat().st_size > 500:
                    return
            except Exception:
                await asyncio.sleep(1.5)
    # Windows SAPI fallback
    wav = out.with_suffix(".wav")
    safe = text.replace('"', "'")
    ps = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = 0
$s.SetOutputToWaveFile('{wav}')
$s.Speak("{safe}")
$s.Dispose()
"""
    subprocess.run(["powershell", "-Command", ps], check=True)
    ffmpeg = r"C:\ffmpeg\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe"
    subprocess.run(
        [ffmpeg, "-y", "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "2", str(out)],
        check=True,
        capture_output=True,
    )
    wav.unlink(missing_ok=True)


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sb = json.loads(STORYBOARD.read_text(encoding="utf-8"))
    for scene in sb["scenes"]:
        sid = scene["id"]
        text = scene.get("narration", "")
        if not text:
            continue
        out = OUT / f"{sid}.mp3"
        print(f"Synthesizing {sid}...")
        await synth(text, out)
        print(f"  -> {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
