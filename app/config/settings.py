"""
Configuration settings for Laplacian AI
"""
import os
from datetime import timedelta
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# GPT/Ollama Configuration
GPT_SERVER_URL = os.getenv('GPT_SERVER_URL', 'http://localhost:11434/api/chat')
GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-oss:20b-cloud')

# Laplacian Lite Configuration (Ollama with phi3:mini)
LITE_MODEL = os.getenv('LITE_MODEL', 'phi3:mini')
LITE_SERVER_URL = os.getenv('GPT_SERVER_URL', 'http://localhost:11434/api/chat')

# Laplacian Coder Configuration
CODER_MODEL = os.getenv('CODER_MODEL', 'qwen3-coder:480b-cloud')

# Laplacian Max Configuration (DeepSeek V3.1)
MAX_MODEL = os.getenv('MAX_MODEL', 'deepseek-v3.1:671b-cloud')

# DocIQ Model Configuration
DOCIQ_MODEL = os.getenv('DOCIQ_MODEL', 'gpt-oss:20b-cloud')
DOCIQ_USE_LITE = False

# Other APIs
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_ID = os.getenv('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')

# Google Search APIs
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '')


def _check_model_available(server_url, model_name):
    """Check if an Ollama model is available by checking model list (faster than generation test)"""
    try:
        print(f"[Laplacian AI] Checking if model exists: {model_name}...")
        # Use /api/tags to list models - much faster than generation test
        base_url = server_url.replace('/api/chat', '')
        response = requests.get(f"{base_url}/api/tags", timeout=10)

        if response.status_code == 200:
            models_data = response.json()
            available_models = [m['name'] for m in models_data.get('models', [])]
            is_available = model_name in available_models
            if is_available:
                print(f"[Laplacian AI] Model {model_name} found in Ollama")
            else:
                print(f"[Laplacian AI] Model {model_name} not found. Available: {available_models}")
            return is_available
        return False
    except requests.exceptions.Timeout:
        print(f"[Laplacian AI] Timeout checking {model_name}")
        return False
    except Exception as e:
        print(f"[Laplacian AI] Error checking {model_name}: {e}")
        return False


# Check model availability at startup
print("[Laplacian AI] Checking model availability...")
LITE_AVAILABLE = _check_model_available(LITE_SERVER_URL, LITE_MODEL)
if LITE_AVAILABLE:
    print(f"[OK] Laplacian Lite model ({LITE_MODEL}) initialized and verified")
else:
    print(f"[WARNING] Laplacian Lite model ({LITE_MODEL}) not available")

CODER_AVAILABLE = _check_model_available(LITE_SERVER_URL, CODER_MODEL)
if CODER_AVAILABLE:
    print(f"[OK] Laplacian Coder model ({CODER_MODEL}) initialized and verified")
else:
    print(f"[WARNING] Laplacian Coder model ({CODER_MODEL}) not available")

MAX_AVAILABLE = _check_model_available(LITE_SERVER_URL, MAX_MODEL)
if MAX_AVAILABLE:
    print(f"[OK] Laplacian Max model ({MAX_MODEL}) initialized and verified")
else:
    print(f"[WARNING] Laplacian Max model ({MAX_MODEL}) not available")

# Default AI Model
DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'gemini' if LITE_AVAILABLE else 'gpt')

# MongoDB flag - initialized in database.py, exposed here for service imports
# This will be updated after database initialization
USE_MONGODB = False

def set_mongodb_status(status):
    """Set MongoDB connection status"""
    global USE_MONGODB
    USE_MONGODB = status


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-change-in-production')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # File uploads
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Model settings
    GPT_SERVER_URL = GPT_SERVER_URL
    GPT_MODEL = GPT_MODEL
    LITE_MODEL = LITE_MODEL
    LITE_SERVER_URL = LITE_SERVER_URL
    CODER_MODEL = CODER_MODEL
    DOCIQ_MODEL = DOCIQ_MODEL

    # API Keys
    ELEVENLABS_API_KEY = ELEVENLABS_API_KEY
    VOICE_ID = VOICE_ID
    GOOGLE_API_KEY = GOOGLE_API_KEY
    GOOGLE_CSE_ID = GOOGLE_CSE_ID


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
