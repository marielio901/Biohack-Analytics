from __future__ import annotations

import asyncio
import re
from functools import lru_cache

import edge_tts


AXIEL_TTS_VOICES = {
    "Antonio": "pt-BR-AntonioNeural",
    "Donato": "pt-BR-DonatoNeural",
}
DEFAULT_AXIEL_VOICE = "Antonio"
MAX_TTS_CHARS = 3500


def prepare_text_for_speech(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""

    replacements = [
        (r"\[([^\]]+)\]\([^)]+\)", r"\1"),
        (r"`([^`]+)`", r"\1"),
        (r"\*\*([^*]+)\*\*", r"\1"),
        (r"__([^_]+)__", r"\1"),
        (r"(?m)^\s*[-*]\s+", ""),
        (r"(?m)^\s*\d+\.\s+", ""),
        (r"[>#*_~|]+", " "),
        (r"\n{2,}", ". "),
        (r"\n", " "),
    ]
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= MAX_TTS_CHARS:
        return cleaned
    return cleaned[:MAX_TTS_CHARS].rsplit(" ", 1)[0].strip() + "..."


async def _stream_edge_tts(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text=text, voice=voice)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)


@lru_cache(maxsize=64)
def synthesize_axiel_audio(text: str, voice_label: str = DEFAULT_AXIEL_VOICE) -> bytes:
    prepared_text = prepare_text_for_speech(text)
    if not prepared_text:
        return b""

    voice = AXIEL_TTS_VOICES.get(voice_label, AXIEL_TTS_VOICES[DEFAULT_AXIEL_VOICE])
    try:
        return asyncio.run(_stream_edge_tts(prepared_text, voice))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_stream_edge_tts(prepared_text, voice))
        finally:
            loop.close()
