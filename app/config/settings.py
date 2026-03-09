"""
Configuration settings for Laplacian AI
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', '')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY', '')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1')

# DocIQ Model Configuration (uses same Azure OpenAI)
DOCIQ_MODEL = AZURE_OPENAI_DEPLOYMENT

# Other APIs
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_ID = os.getenv('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')

# Google Search APIs
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '')

# Check Azure OpenAI availability at startup
AZURE_AVAILABLE = bool(AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY)
if AZURE_AVAILABLE:
    print(f"[OK] Azure OpenAI configured (deployment: {AZURE_OPENAI_DEPLOYMENT})")
else:
    print("[WARNING] Azure OpenAI not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")

# Default AI Model
DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'gpt')

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

    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT = AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY = AZURE_OPENAI_API_KEY
    AZURE_OPENAI_API_VERSION = AZURE_OPENAI_API_VERSION
    AZURE_OPENAI_DEPLOYMENT = AZURE_OPENAI_DEPLOYMENT
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
