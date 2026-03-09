"""
Constants for Laplacian AI
"""
from app.config.settings import AZURE_OPENAI_DEPLOYMENT, AZURE_AVAILABLE

# Allowed file extensions for DocIQ
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

# Allowed file extensions for VizIQ
VIZIQ_ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}

# AI Models Configuration (all powered by Azure OpenAI gpt-4.1)
AI_MODELS = {
    'gpt': {
        'name': 'LAPLACIAN Core',
        'description': f'Azure OpenAI ({AZURE_OPENAI_DEPLOYMENT})',
        'available': AZURE_AVAILABLE
    },
    'gemini': {
        'name': 'LAPLACIAN Lite',
        'description': f'Azure OpenAI ({AZURE_OPENAI_DEPLOYMENT})',
        'available': AZURE_AVAILABLE
    },
    'coder': {
        'name': 'LAPLACIAN Coder',
        'description': f'Code Expert ({AZURE_OPENAI_DEPLOYMENT})',
        'available': AZURE_AVAILABLE
    },
    'max': {
        'name': 'LAPLACIAN Max',
        'description': f'Ultimate AI ({AZURE_OPENAI_DEPLOYMENT})',
        'available': AZURE_AVAILABLE
    }
}

# Piston API for code execution
PISTON_API_URL = "https://emkc.org/api/v2/piston/execute"

# Language mapping for Piston API
PISTON_LANGUAGES = {
    'python': {'language': 'python', 'version': '3.10.0'},
    'py': {'language': 'python', 'version': '3.10.0'},
    'javascript': {'language': 'javascript', 'version': '18.15.0'},
    'js': {'language': 'javascript', 'version': '18.15.0'},
    'java': {'language': 'java', 'version': '15.0.2'},
    'cpp': {'language': 'cpp', 'version': '10.2.0'},
    'c++': {'language': 'cpp', 'version': '10.2.0'},
    'c': {'language': 'c', 'version': '10.2.0'},
    'go': {'language': 'go', 'version': '1.16.2'},
    'rust': {'language': 'rust', 'version': '1.68.2'},
    'ruby': {'language': 'ruby', 'version': '3.0.1'},
    'php': {'language': 'php', 'version': '8.2.3'},
}

# File extension mapping for code execution
CODE_FILE_EXTENSIONS = {
    'python': 'py',
    'javascript': 'js',
    'java': 'java',
    'cpp': 'cpp',
    'c': 'c',
    'go': 'go',
    'rust': 'rs',
    'ruby': 'rb',
    'php': 'php'
}
