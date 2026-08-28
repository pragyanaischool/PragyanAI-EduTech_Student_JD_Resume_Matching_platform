import io
import tempfile
import os
from gtts import gTTS
from groq import Groq
from config.settings import settings


def get_groq_client() -> Groq:
    """Instantiate and return the Groq SDK client."""
    return Groq(api_key=settings.GROQ_API_KEY)


def generate_tts_audio(text: str, lang: str = "en") -> bytes:
    """
    Synthesizes speech audio from text using gTTS.
    Returns the raw MP3 audio bytes for direct playback in Streamlit.
    """
    clean_text = text.replace("**", "").replace("#", "").replace("- ", "").strip()
    if not clean_text:
        clean_text = "No question text provided."

    tts = gTTS(text=clean_text, lang=lang, slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribes audio bytes into text using Groq's accelerated Whisper endpoint.
    Handles WAV/MP3 bytes recorded directly from Streamlit audio components.
    """
    if not audio_bytes:
        return ""

    if not settings.GROQ_API_KEY:
        return "Simulated transcription: Candidate provided verbal response (GROQ_API_KEY not configured)."

    client = get_groq_client()

    # Write temporarily to disk for standard file pointer upload to Groq API
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as file_handle:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(temp_audio_path), file_handle.read()),
                model=settings.WHISPER_MODEL,
                response_format="text",
                language="en",
                temperature=0.0
            )
        return str(transcription).strip()
    except Exception as e:
        return f"Audio transcription error: {str(e)}"
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
          
