"""
Configuration settings for Laplacian AI
"""
import os
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

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

# Check Azure OpenAI availability at startup
AZURE_AVAILABLE = bool(AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY)
if AZURE_AVAILABLE:
    print(f"[OK] Azure OpenAI configured (deployment: {AZURE_OPENAI_DEPLOYMENT})")
else:
    print("[WARNING] Azure OpenAI not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")

# Default AI Model
DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'gpt')

# MongoDB flag - initialized in database.py, exposed here for service imports
USE_MONGODB = False


def set_mongodb_status(status):
    """Set MongoDB connection status"""
    global USE_MONGODB
    USE_MONGODB = status

# Max upload size (16 MB)
MAX_UPLOAD_SIZE = 16 * 1024 * 1024
