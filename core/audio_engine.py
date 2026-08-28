import io
import os
from typing import Optional
import streamlit as st
from groq import Groq
from gtts import gTTS
from config.settings import settings


# ==============================================================================
# Groq Client Resolver
# ==============================================================================
def get_groq_client() -> Groq:
    """
    Initializes Groq client with fallback precedence:
    1. settings.GROQ_API_KEY
    2. st.secrets["GROQ_API_KEY"]
    3. os.environ["GROQ_API_KEY"]
    """
    api_key = ""
    if getattr(settings, "GROQ_API_KEY", None):
        api_key = str(settings.GROQ_API_KEY).strip()

    if not api_key:
        try:
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = str(st.secrets["GROQ_API_KEY"]).strip()
        except Exception:
            pass

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY", "").strip()

    return Groq(api_key=api_key)


# ==============================================================================
# Text-to-Speech (TTS) Engine
# ==============================================================================
def text_to_speech_audio(text: str, lang: str = "en") -> Optional[bytes]:
    """
    Synthesizes speech audio (MP3 format) in-memory from text input using gTTS.
    Returns bytes suitable for st.audio() playback.
    """
    if not text or not text.strip():
        return None

    try:
        clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
        tts = gTTS(text=clean_text[:500], lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.getvalue()
    except Exception as e:
        print(f"[!] TTS Generation warning: {str(e)}")
        return None


# ==============================================================================
# Speech-to-Text (STT) Whisper Engine
# ==============================================================================
def transcribe_audio_whisper(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribes spoken voice audio (WAV, MP3, M4A, OGG) using Groq Whisper.
    """
    if not audio_bytes:
        return ""

    try:
        client = get_groq_client()
        whisper_model = getattr(settings, "WHISPER_MODEL", "whisper-large-v3-turbo")

        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model=whisper_model,
            response_format="json",
            temperature=0.0
        )
        return getattr(transcription, "text", str(transcription)).strip()
    except Exception as e:
        st.error(f"Whisper transcription failed: {str(e)}")
        return ""


# ==============================================================================
# Backward-Compatible Function Aliases
# ==============================================================================
generate_tts_audio = text_to_speech_audio
synthesize_speech = text_to_speech_audio
transcribe_audio = transcribe_audio_whisper
transcribe_voice = transcribe_audio_whisper
