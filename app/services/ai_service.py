"""
AI Service - Handles AI response generation
"""
import requests
import json
from datetime import datetime
from flask import session

from app.config.settings import (
    GPT_SERVER_URL, GPT_MODEL,
    LITE_SERVER_URL, LITE_MODEL,
    CODER_MODEL, DEFAULT_AI_MODEL
)
from app.config.constants import AI_MODELS


def get_system_prompt():
    """Get the system prompt with current date/time"""
    return f"""You are Laplacian by Perfionix AI – a professional coding assistant and programming expert with web search capabilities.

You help developers with:
- Writing, debugging, and optimizing code
- Explaining algorithms and data structures
- Code reviews and best practices
- Problem-solving and architecture design
- Learning new programming concepts
- Searching the web for latest information

WEB SEARCH CAPABILITY:
You have access to real-time web search. When you receive search results, use them to provide accurate, up-to-date information.
- Cite sources when using search results
- Summarize key findings clearly
- Provide links when relevant

IMPORTANT FORMATTING RULES:
- Always use proper markdown formatting
- Wrap code in triple backticks with language specification (```python, ```javascript, etc.)
- Use inline code with single backticks for variable names, functions, etc.
- Structure responses with headers, lists, and clear sections
- Be concise but thorough
- Include code examples when helpful

MERMAID DIAGRAM RULES (CRITICAL):
When creating Mermaid diagrams, you MUST follow these syntax rules to avoid parse errors:
- ALWAYS quote node text that contains special characters: parentheses (), brackets [], braces {{}}, quotes, or angle brackets <>
- Use double quotes for node content: A["text with (parens)"] NOT A[text with (parens)]
- Examples of CORRECT syntax:
  * A["Request Body (POST/PUT)"] ✓
  * B["Array[0] = value"] ✓
  * C["Check if x > 0"] ✓
  * D["User's input"] ✓
- Examples of WRONG syntax (will cause parse errors):
  * A[Request Body (POST/PUT)] ✗ - parentheses break parsing
  * B[Array[0] = value] ✗ - brackets break parsing
  * C[Check if x > 0] ✗ - angle brackets break parsing
- For simple text without special chars, quotes are optional: A[Simple Text] is fine
- Use <br/> for line breaks inside quoted text: A["Line 1<br/>Line 2"]

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""


def get_current_model():
    """Get the current AI model from session"""
    if 'ai_model' not in session:
        session['ai_model'] = DEFAULT_AI_MODEL
        session.modified = True
    return session['ai_model']


def set_current_model(model):
    """Set the current AI model in session"""
    if model in AI_MODELS and AI_MODELS[model]['available']:
        session['ai_model'] = model
        session.modified = True
        return True
    return False


def generate_gpt_response(conversation):
    """Generate AI response using GPT/Ollama"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": GPT_MODEL,
        "messages": conversation,
        "stream": False,
        "options": {
            "num_predict": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    }

    try:
        print(f"[Laplacian Core] Using model: {GPT_MODEL}")
        print(f"[Laplacian Core] Sending request to: {GPT_SERVER_URL}")

        response = requests.post(GPT_SERVER_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        if "message" in data and "content" in data["message"]:
            content = data["message"]["content"]
            print(f"[Laplacian Core] Response received: {len(content)} characters")
            return content

        print(f"[Laplacian Core] Unexpected response format: {data}")
        return "Sorry, I couldn't process that request."

    except requests.exceptions.Timeout:
        print(f"[Laplacian Core] Request timed out")
        return "Request timed out. The model is taking too long to respond. Please try again."
    except requests.exceptions.ConnectionError as e:
        print(f"[Laplacian Core] Connection error: {str(e)}")
        return f"Connection error: Unable to reach Ollama server. Please ensure Ollama is running with {GPT_MODEL} model pulled."
    except requests.exceptions.HTTPError as e:
        print(f"[Laplacian Core] HTTP error: {str(e)}")
        if "404" in str(e):
            return f"Model '{GPT_MODEL}' not found. Please run: ollama pull {GPT_MODEL}"
        return f"HTTP error occurred: {str(e)}"
    except requests.exceptions.RequestException as e:
        print(f"[Laplacian Core] Request error: {str(e)}")
        return f"Connection error: Unable to reach AI server. Please ensure Ollama is running."
    except json.JSONDecodeError as e:
        print(f"[Laplacian Core] JSON decode error: {str(e)}")
        return "Error parsing response from the model. Please try again."
    except Exception as e:
        print(f"[Laplacian Core] Unexpected error: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"


def generate_lite_response(conversation):
    """Generate AI response using Ollama with Lite model (phi3:mini)"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": LITE_MODEL,
        "messages": conversation,
        "stream": False,
        "options": {
            "num_predict": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    }

    try:
        print(f"[Laplacian Lite] Using model: {LITE_MODEL}")
        print(f"[Laplacian Lite] Sending request to: {LITE_SERVER_URL}")

        response = requests.post(LITE_SERVER_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        if "message" in data and "content" in data["message"]:
            content = data["message"]["content"]
            print(f"[Laplacian Lite] Response received: {len(content)} characters")
            return content

        print(f"[Laplacian Lite] Unexpected response format: {data}")
        return "Sorry, I couldn't process that request with Laplacian Lite."

    except requests.exceptions.Timeout:
        print(f"[Laplacian Lite] Request timed out")
        return "Request timed out. The model is taking too long to respond. Please try again."
    except requests.exceptions.ConnectionError as e:
        print(f"[Laplacian Lite] Connection error: {str(e)}")
        return f"Connection error: Unable to reach Ollama server. Please ensure Ollama is running with {LITE_MODEL} model pulled."
    except requests.exceptions.HTTPError as e:
        print(f"[Laplacian Lite] HTTP error: {str(e)}")
        if "404" in str(e):
            return f"Model '{LITE_MODEL}' not found. Please run: ollama pull {LITE_MODEL}"
        return f"HTTP error occurred: {str(e)}"
    except requests.exceptions.RequestException as e:
        print(f"[Laplacian Lite] Request error: {str(e)}")
        return f"Connection error: Unable to reach Ollama server for Laplacian Lite. Please ensure Ollama is running."
    except json.JSONDecodeError as e:
        print(f"[Laplacian Lite] JSON decode error: {str(e)}")
        return "Error parsing response from the model. Please try again."
    except Exception as e:
        print(f"[Laplacian Lite] Unexpected error: {str(e)}")
        return f"An unexpected error occurred with Laplacian Lite: {str(e)}"


def generate_coder_response(conversation):
    """Generate AI response using Ollama with Qwen3 Coder model for coding tasks"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": CODER_MODEL,
        "messages": conversation,
        "stream": False,
        "options": {
            "num_predict": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    }

    try:
        print(f"[Laplacian Coder] Using model: {CODER_MODEL}")
        print(f"[Laplacian Coder] Sending request to: {LITE_SERVER_URL}")

        response = requests.post(LITE_SERVER_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        if "message" in data and "content" in data["message"]:
            content = data["message"]["content"]
            print(f"[Laplacian Coder] Response received: {len(content)} characters")
            return content

        print(f"[Laplacian Coder] Unexpected response format: {data}")
        return "Sorry, I couldn't process that request with Laplacian Coder."

    except requests.exceptions.Timeout:
        print(f"[Laplacian Coder] Request timed out")
        return "Request timed out. The model is taking too long to respond. Please try again."
    except requests.exceptions.ConnectionError as e:
        print(f"[Laplacian Coder] Connection error: {str(e)}")
        return f"Connection error: Unable to reach Ollama server. Please ensure Ollama is running with {CODER_MODEL} model pulled."
    except requests.exceptions.HTTPError as e:
        print(f"[Laplacian Coder] HTTP error: {str(e)}")
        if "404" in str(e):
            return f"Model '{CODER_MODEL}' not found. Please run: ollama pull {CODER_MODEL}"
        return f"HTTP error occurred: {str(e)}"
    except requests.exceptions.RequestException as e:
        print(f"[Laplacian Coder] Request error: {str(e)}")
        return f"Connection error: Unable to reach Ollama server for Laplacian Coder. Please ensure Ollama is running."
    except json.JSONDecodeError as e:
        print(f"[Laplacian Coder] JSON decode error: {str(e)}")
        return "Error parsing response from the model. Please try again."
    except Exception as e:
        print(f"[Laplacian Coder] Unexpected error: {str(e)}")
        return f"An unexpected error occurred with Laplacian Coder: {str(e)}"


def generate_ai_response(conversation, model=None):
    """Generate AI response from conversation history using selected model"""
    current_model = model or get_current_model()

    if current_model == 'gemini':
        return generate_lite_response(conversation)
    elif current_model == 'coder':
        return generate_coder_response(conversation)
    else:
        return generate_gpt_response(conversation)
