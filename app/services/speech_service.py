"""
Speech Service - Text-to-speech functionality
"""
import requests
from app.config.settings import ELEVENLABS_API_KEY, VOICE_ID


def generate_speech(text):
    """Generate speech using ElevenLabs API"""
    if not ELEVENLABS_API_KEY:
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "expressiveness": 0.9
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"[Speech] Error generating speech: {str(e)}")
        return None
