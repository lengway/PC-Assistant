"""Text-to-speech via edge-tts."""

import asyncio
from typing import Optional

import edge_tts

DEFAULT_VOICE = "ru-RU-DmitryNeural"


async def speak_async(text: str, voice: str = DEFAULT_VOICE, rate: Optional[str] = None) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.stream()  # plays audio through default output


def speak(text: str, voice: str = DEFAULT_VOICE, rate: Optional[str] = None) -> None:
    asyncio.run(speak_async(text, voice=voice, rate=rate))
