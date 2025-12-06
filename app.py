from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import requests
import json
from datetime import datetime, timedelta
from io import BytesIO
import threading
import uuid
import re

# Load environment variables
load_dotenv()

# Import database module
from database import init_database, get_database

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# DocIQ Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------
# Configuration
# -------------------------------

# GPT/Ollama Configuration
GPT_SERVER_URL = os.getenv('GPT_SERVER_URL', 'http://localhost:11434/api/chat')
GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-oss:120b-cloud')

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# Initialize Gemini client
gemini_client = None
GEMINI_AVAILABLE = False
if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        print("[OK] Gemini client initialized")
    except Exception as e:
        print(f"[WARNING] Failed to initialize Gemini client: {e}")
        GEMINI_AVAILABLE = False

# Other APIs
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_ID = os.getenv('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')

# Default AI Model
DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'gemini' if GEMINI_AVAILABLE else 'gpt')

# Available AI Models
AI_MODELS = {
    'gpt': {
        'name': 'AXIO Core',
        'description': 'Local GPT model via Ollama',
        'available': True
    },
    'gemini': {
        'name': 'AXIO Lite',
        'description': 'Perfionix AI',
        'available': GEMINI_AVAILABLE
    }
}

# Initialize MongoDB connection
USE_MONGODB = init_database()
db = get_database()

# Fallback in-memory storage (used when MongoDB is not available)
user_data = {
    'notes': [],
    'reminders': [],
    'tasks': []
}

# DocIQ document storage (fallback)
dociq_storage = {}

# Simple fallback: single-user mode storage (for development/testing)
dociq_single_user_storage = {
    'documents': [],
    'conversation': []
}

# VizIQ storage (fallback)
viziq_storage = {
    'data': None,
    'columns': [],
    'dtypes': {},
    'filename': '',
    'analysis': None
}

# -------------------------------
# AI Chat Functions
# -------------------------------

def get_system_prompt():
    """Get the system prompt with current date/time"""
    return f"""You are Axio by Perfionix AI – a professional coding assistant and programming expert with web search capabilities.

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

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""


def get_session_id():
    """Get or create session ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.modified = True
    return session['session_id']

def get_conversation():
    """Get or initialize conversation for current session"""
    session_id = get_session_id()

    # Try to get from MongoDB first
    if USE_MONGODB and db.is_connected():
        messages = db.get_chat_history(session_id, limit=50)
        if messages:
            # Convert to conversation format
            conversation = [{"role": "system", "content": get_system_prompt()}]
            for msg in messages:
                conversation.append({
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "_id": msg.get("id")  # Store MongoDB ID for editing
                })
            return conversation

    # Fallback to session storage
    if 'conversation' not in session:
        session['conversation'] = [
            {
                "role": "system",
                "content": get_system_prompt()
            }
        ]
        session.modified = True
    return session['conversation']

def save_conversation(conversation):
    """Save conversation to session and MongoDB"""
    session_id = get_session_id()

    # Save to MongoDB if connected
    if USE_MONGODB and db.is_connected():
        # Get the last two messages (user + assistant) to save
        if len(conversation) >= 2:
            # Check if these are new messages (don't have _id)
            for msg in conversation[-2:]:
                if msg.get("role") in ["user", "assistant"] and "_id" not in msg:
                    msg_id = db.save_chat_message(
                        session_id=session_id,
                        role=msg["role"],
                        content=msg["content"],
                        metadata={"searched": msg.get("searched", False)}
                    )
                    msg["_id"] = msg_id

    # Also save to session as backup
    session['conversation'] = conversation
    session.modified = True

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
        response = requests.post(GPT_SERVER_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        return "Sorry, I couldn't process that request."

    except requests.exceptions.RequestException as e:
        return f"Connection error: Unable to reach AI server. Please ensure the GPT server is running."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def generate_gemini_response(conversation):
    """Generate AI response using Google Gemini SDK"""
    if not gemini_client:
        return "Gemini client not initialized. Please check your GEMINI_API_KEY in .env file."

    try:
        # Log which model is being used
        print(f"[Gemini] Using model: {GEMINI_MODEL}")

        # Extract system prompt
        system_prompt = next((msg['content'] for msg in conversation if msg.get('role') == 'system'), None)

        # Build the conversation content for Gemini
        # Combine all messages into a single prompt with context
        prompt_parts = []

        if system_prompt:
            prompt_parts.append(f"[System Instructions]\n{system_prompt}\n\n[Conversation]")

        for msg in conversation:
            role = msg.get('role', '')
            content = msg.get('content', '')

            if role == 'system':
                continue
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")

        # Add instruction to continue as assistant
        prompt_parts.append("Assistant:")

        full_prompt = "\n\n".join(prompt_parts)

        # Generate response using the SDK
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt
        )

        if response and response.text:
            return response.text
        else:
            return "Sorry, I couldn't generate a response with Gemini."

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Gemini API error: {error_msg}")

        if "blocked" in error_msg.lower():
            return "The response was blocked by Gemini's safety filters. Please try rephrasing your question."
        elif "quota" in error_msg.lower():
            return "Gemini API quota exceeded. Please try again later."
        else:
            return f"An error occurred with Gemini: {error_msg}"

def generate_ai_response(conversation, model=None):
    """Generate AI response from conversation history using selected model"""
    # Use specified model or get current model from session
    current_model = model or get_current_model()

    if current_model == 'gemini':
        return generate_gemini_response(conversation)
    else:
        return generate_gpt_response(conversation)

def should_search_web(message: str) -> bool:
    """Determine if the message requires a web search"""
    message_lower = message.lower()

    # Keywords that indicate a search is needed
    search_keywords = [
        'search', 'google', 'find', 'look up', 'lookup', 'what is', 'who is',
        'when did', 'where is', 'how to', 'latest', 'recent', 'news', 'current',
        'today', 'update', 'trending', '2024', '2025', 'price', 'weather',
        'definition', 'meaning', 'explain what', 'tell me about', 'information about',
        'search for', 'search the web', 'web search', 'online', 'internet'
    ]

    # Check for search indicators
    for keyword in search_keywords:
        if keyword in message_lower:
            return True

    # Check for question patterns that might need current info
    question_patterns = ['what is the', 'who is the', 'when is', 'where is the', 'how do i', 'how can i']
    for pattern in question_patterns:
        if message_lower.startswith(pattern):
            return True

    return False


def chat_with_ai(user_message: str, force_search: bool = False):
    """Send message to AI and get response, with optional web search"""
    conversation = get_conversation()

    # Check if we should perform a web search
    search_results = None
    if force_search or should_search_web(user_message):
        print(f"Performing web search for: {user_message}")
        search_results = web_search(user_message)
        print(f"Search results: {len(search_results) if search_results else 0} results found")

    # Build the user message with search results if available
    if search_results:
        search_context = "\n\n📊 **Web Search Results:**\n\n"
        for i, result in enumerate(search_results, 1):
            search_context += f"**{i}. {result.get('title', 'No title')}**\n"
            if result.get('snippet'):
                search_context += f"{result['snippet']}\n"
            if result.get('link'):
                search_context += f"🔗 {result['link']}\n"
            search_context += "\n"

        enhanced_message = f"{user_message}\n{search_context}\nPlease use the above search results to provide an accurate and helpful response. Cite sources when relevant."
    else:
        enhanced_message = user_message

    # Add user message (original, not enhanced)
    user_msg_obj = {"role": "user", "content": user_message}
    conversation.append(user_msg_obj)
    user_index = len(conversation) - 1

    # Create a temporary conversation with enhanced message for AI
    temp_conversation = conversation.copy()
    temp_conversation[-1] = {"role": "user", "content": enhanced_message}

    # Get AI response
    ai_response_text = generate_ai_response(temp_conversation)

    # Add AI response
    ai_msg_obj = {"role": "assistant", "content": ai_response_text}
    conversation.append(ai_msg_obj)
    ai_index = len(conversation) - 1

    save_conversation(conversation)
    return ai_response_text, user_index, ai_index, bool(search_results)

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
    except:
        return None

# -------------------------------
# Web Search Function
# -------------------------------

# Google Custom Search API configuration (optional - for better reliability)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '')

def web_search(query):
    """Perform web search - tries multiple methods"""
    print(f"[SEARCH] Starting web search for: {query}")

    # Method 1: Try Google Custom Search API (most reliable if configured)
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        results = web_search_google_api(query)
        if results:
            print(f"[OK] Google Custom Search API returned {len(results)} results")
            return results

    # Method 2: Try DuckDuckGo (most reliable free option)
    results = web_search_duckduckgo(query)
    if results:
        print(f"[OK] DuckDuckGo returned {len(results)} results")
        return results

    # Method 3: Try googlesearch-python library
    results = web_search_googlesearch(query)
    if results:
        print(f"[OK] googlesearch-python returned {len(results)} results")
        return results

    # Method 4: Fallback to direct Google scraping
    results = web_search_google_scrape(query)
    if results:
        print(f"[OK] Google scrape returned {len(results)} results")
        return results

    print("[ERROR] All search methods failed")
    return []


def web_search_google_api(query):
    """Search using Google Custom Search JSON API"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': 5
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get('items', []):
            results.append({
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
                'link': item.get('link', '')
            })

        return results if results else None
    except Exception as e:
        print(f"Google API error: {e}")
        return None


def web_search_duckduckgo(query):
    """Search using DuckDuckGo HTML"""
    import urllib.parse
    from bs4 import BeautifulSoup

    try:
        search_url = "https://html.duckduckgo.com/html/"
        data = {'q': query}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://html.duckduckgo.com',
            'Referer': 'https://html.duckduckgo.com/'
        }

        response = requests.post(search_url, data=data, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Find search results
        for result in soup.find_all('div', class_='result')[:5]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')

            if title_elem:
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')

                # Clean DuckDuckGo redirect URL
                if 'uddg=' in link:
                    link = urllib.parse.unquote(link.split('uddg=')[1].split('&')[0])

                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                if title and link and link.startswith('http'):
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'link': link
                    })

        return results if results else None
    except Exception as e:
        print(f"DuckDuckGo error: {e}")
        return None


def web_search_googlesearch(query):
    """Search using googlesearch-python library"""
    try:
        from googlesearch import search
        import time

        results = []
        # Add delay to avoid rate limiting
        time.sleep(1)

        try:
            search_results = list(search(query, num_results=5, advanced=True, sleep_interval=2))
        except TypeError:
            # Fallback for older version without sleep_interval
            search_results = list(search(query, num_results=5, advanced=True))

        for result in search_results:
            results.append({
                'title': result.title if hasattr(result, 'title') else '',
                'snippet': result.description if hasattr(result, 'description') else '',
                'link': result.url if hasattr(result, 'url') else ''
            })
        return results if results else None
    except Exception as e:
        print(f"googlesearch error: {e}")
        return None


def web_search_google_scrape(query):
    """Fallback web search using direct Google scraping"""
    import urllib.parse
    from bs4 import BeautifulSoup
    import random
    import time

    # Random delay to avoid detection
    time.sleep(random.uniform(1, 3))

    search_url = "https://www.google.com/search"
    params = {
        'q': query,
        'num': 10,
        'hl': 'en',
        'safe': 'off'
    }

    # Rotate user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
    ]

    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

    try:
        session = requests.Session()
        response = session.get(search_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Try multiple selectors for search results
        search_divs = soup.find_all('div', class_='g')

        # Alternative selector if 'g' class doesn't work
        if not search_divs:
            search_divs = soup.select('div[data-hveid]')

        # Another fallback
        if not search_divs:
            search_divs = soup.find_all('div', {'class': lambda x: x and 'g' in x.split()})

        for div in search_divs[:5]:
            try:
                # Get title - try multiple selectors
                title_elem = div.find('h3') or div.find('h2') or div.select_one('[role="heading"]')
                title = title_elem.get_text(strip=True) if title_elem else ''

                # Get link
                link_elem = div.find('a', href=True)
                link = link_elem.get('href', '') if link_elem else ''

                # Clean the link
                if link.startswith('/url?q='):
                    link = link.split('/url?q=')[1].split('&')[0]
                    link = urllib.parse.unquote(link)
                elif link.startswith('/search'):
                    continue  # Skip internal Google links

                # Skip if not a valid URL
                if not link.startswith('http'):
                    continue

                # Get snippet - try multiple selectors
                snippet_elem = (
                    div.find('div', class_='VwiC3b') or
                    div.find('span', class_='aCOpRe') or
                    div.select_one('[data-sncf]') or
                    div.find('div', {'style': lambda x: x and 'line-clamp' in str(x)})
                )
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                if title and link:
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'link': link
                    })

            except Exception as e:
                continue

        return results if results else None

    except Exception as e:
        print(f"Google scrape error: {e}")
        return None

# -------------------------------
# DocIQ - Document Intelligence Functions
# -------------------------------

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text.strip()
    except ImportError:
        # Fallback: try pdfplumber
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            return text.strip()
        except ImportError:
            return "Error: PDF parsing library not installed. Please install PyPDF2 or pdfplumber."
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from Word document"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except ImportError:
        return "Error: python-docx library not installed. Please install it using: pip install python-docx"
    except Exception as e:
        return f"Error extracting Word document text: {str(e)}"

def extract_text_from_txt(file_path):
    """Extract text from plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            return f"Error reading text file: {str(e)}"
    except Exception as e:
        return f"Error reading text file: {str(e)}"

def extract_text_from_document(file_path, file_extension):
    """Extract text from document based on file type"""
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['doc', 'docx']:
        return extract_text_from_docx(file_path)
    elif file_extension == 'txt':
        return extract_text_from_txt(file_path)
    else:
        return "Unsupported file format"

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks for better context retrieval"""
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Try to find a natural break point (paragraph or sentence)
        if end < text_length:
            # Look for paragraph break
            para_break = text.rfind('\n\n', start, end)
            if para_break > start + chunk_size // 2:
                end = para_break
            else:
                # Look for sentence break
                sentence_break = max(
                    text.rfind('. ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('! ', start, end)
                )
                if sentence_break > start + chunk_size // 2:
                    end = sentence_break + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < text_length else text_length

    return chunks

def get_dociq_session_id():
    """Get or create DocIQ session ID"""
    if 'dociq_session_id' not in session:
        session['dociq_session_id'] = str(uuid.uuid4())
        session.modified = True
        print(f"[DocIQ] Created new session ID: {session['dociq_session_id']}")
    return session['dociq_session_id']

def get_dociq_documents():
    """Get documents for current session - uses MongoDB or fallback storage"""
    session_id = get_dociq_session_id()

    # Try MongoDB first
    if USE_MONGODB and db.is_connected():
        documents = db.get_dociq_documents(session_id)
        conversation = db.get_dociq_conversation(session_id)
        doc_count = len(documents)
        print(f"[DocIQ] Using MongoDB storage with {doc_count} documents")
        return {
            'documents': documents,
            'conversation': [{'role': msg['role'], 'content': msg['content']} for msg in conversation]
        }

    # Fallback to in-memory storage
    doc_count = len(dociq_single_user_storage['documents'])
    print(f"[DocIQ] Using single-user mode storage with {doc_count} documents")
    return dociq_single_user_storage

def get_combined_document_context(session_data, max_context_length=8000):
    """Get combined context from all documents"""
    all_chunks = []
    for doc in session_data['documents']:
        if doc.get('chunks'):
            all_chunks.extend(doc['chunks'][:5])  # Take first 5 chunks from each doc

    # Combine chunks up to max context length
    context = ""
    for chunk in all_chunks:
        if len(context) + len(chunk) < max_context_length:
            context += chunk + "\n\n---\n\n"
        else:
            break

    return context

def search_documents(query, session_data, max_results=5):
    """Simple keyword-based search across documents"""
    query_words = set(query.lower().split())
    results = []

    for doc in session_data['documents']:
        for chunk in doc.get('chunks', []):
            chunk_lower = chunk.lower()
            # Count matching words
            matches = sum(1 for word in query_words if word in chunk_lower)
            if matches > 0:
                results.append({
                    'chunk': chunk,
                    'doc_name': doc['name'],
                    'score': matches / len(query_words)
                })

    # Sort by score and return top results
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]

def generate_dociq_response(user_message, session_data):
    """Generate AI response based on document context"""
    # Search for relevant chunks
    relevant_chunks = search_documents(user_message, session_data)

    # Build context from relevant chunks
    if relevant_chunks:
        context = "**Relevant Document Content:**\n\n"
        for i, result in enumerate(relevant_chunks, 1):
            context += f"[From: {result['doc_name']}]\n{result['chunk']}\n\n---\n\n"
    else:
        # If no specific matches, use general document context
        context = get_combined_document_context(session_data)
        if context:
            context = "**Document Content:**\n\n" + context

    if not context:
        return "I don't have any document content to reference. Please upload some documents first."

    # Create conversation with document context
    conversation = [
        {
            "role": "system",
            "content": f"""You are DocIQ, an intelligent document assistant by Perfionix AI.
You help users understand, analyze, and extract information from their uploaded documents.

IMPORTANT GUIDELINES:
- Base your answers ONLY on the document content provided below
- If the information is not in the documents, clearly state that
- Quote relevant passages when appropriate
- Be precise and accurate
- If asked to summarize, provide key points
- If asked to compare, highlight differences and similarities
- Always cite which document the information comes from

UPLOADED DOCUMENT CONTENT:
{context}

Current date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    # Add conversation history
    for msg in session_data['conversation'][-6:]:  # Keep last 6 messages for context
        if msg['role'] in ['user', 'assistant']:
            conversation.insert(-1, msg)

    return generate_ai_response(conversation)

# -------------------------------
# Routes
# -------------------------------

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

# -------------------------------
# Model Selection Routes
# -------------------------------

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available AI models"""
    current_model = get_current_model()
    models_info = []

    for model_id, model_data in AI_MODELS.items():
        models_info.append({
            'id': model_id,
            'name': model_data['name'],
            'description': model_data['description'],
            'available': model_data['available'],
            'active': model_id == current_model
        })

    return jsonify({
        'models': models_info,
        'current': current_model
    })

@app.route('/api/models/select', methods=['POST'])
def select_model():
    """Select an AI model"""
    data = request.json
    model_id = data.get('model', '')

    if not model_id:
        return jsonify({'error': 'No model specified'}), 400

    if model_id not in AI_MODELS:
        return jsonify({'error': 'Invalid model'}), 400

    if not AI_MODELS[model_id]['available']:
        return jsonify({'error': f'{AI_MODELS[model_id]["name"]} is not available. Check API configuration.'}), 400

    if set_current_model(model_id):
        return jsonify({
            'success': True,
            'model': model_id,
            'name': AI_MODELS[model_id]['name'],
            'message': f'Switched to {AI_MODELS[model_id]["name"]}'
        })

    return jsonify({'error': 'Failed to switch model'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')
    force_search = data.get('search', False)

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    ai_response, user_idx, ai_idx, searched = chat_with_ai(user_message, force_search)
    current_model = get_current_model()

    return jsonify({
        'response': ai_response,
        'user_index': user_idx,
        'ai_index': ai_idx,
        'searched': searched,
        'model': current_model,
        'model_name': AI_MODELS[current_model]['name'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/chat/edit', methods=['POST'])
def edit_chat():
    """Edit a message and regenerate response"""
    data = request.json

    # Debug logging
    print(f"Edit request data: {data}")

    # Handle index
    index_value = data.get('index')
    if index_value is None:
        return jsonify({'error': 'Invalid index - index is None'}), 400

    try:
        message_index = int(index_value)
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid index - cannot convert: {index_value}'}), 400

    new_content = data.get('content')
    if not new_content:
        return jsonify({'error': 'No content provided'}), 400

    conversation = get_conversation()

    # Debug logging
    print(f"Conversation length: {len(conversation)}, Requested index: {message_index}")
    for i, msg in enumerate(conversation):
        print(f"  [{i}] {msg['role']}: {msg['content'][:50]}...")

    # Validate index (must be >= 1 because index 0 is system message)
    if message_index < 1 or message_index >= len(conversation):
        return jsonify({'error': f'Invalid index - out of range. Index: {message_index}, Conversation length: {len(conversation)}'}), 400

    # Verify we're editing a user message
    if conversation[message_index]['role'] != 'user':
        return jsonify({'error': 'Can only edit user messages'}), 400

    # Update the message
    conversation[message_index]['content'] = new_content

    # Remove everything after this message (truncate history)
    # We keep the edited message (at message_index), remove subsequent ones
    del conversation[message_index+1:]

    # Generate new response based on updated history
    ai_response_text = generate_ai_response(conversation)

    # Append new AI response
    conversation.append({"role": "assistant", "content": ai_response_text})
    ai_index = len(conversation) - 1

    save_conversation(conversation)

    return jsonify({
        'response': ai_response_text,
        'user_index': message_index,
        'ai_index': ai_index,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """Reset conversation"""
    session_id = get_session_id()

    # Clear from MongoDB
    if USE_MONGODB and db.is_connected():
        db.clear_chat_history(session_id)

    # Clear from session
    session.pop('conversation', None)
    return jsonify({'status': 'success', 'message': 'Conversation reset'})

@app.route('/api/chat/debug', methods=['GET'])
def debug_chat():
    """Debug endpoint to check conversation state"""
    conversation = get_conversation()
    return jsonify({
        'length': len(conversation),
        'messages': [{'index': i, 'role': m['role'], 'content': m['content'][:100]} for i, m in enumerate(conversation)]
    })

@app.route('/api/search', methods=['POST'])
def search():
    """Perform web search and optionally get AI summary"""
    data = request.json
    query = data.get('query', '')
    summarize = data.get('summarize', False)

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Perform web search
    results = web_search(query)

    if not results:
        return jsonify({
            'results': [],
            'summary': 'No search results found.',
            'query': query
        })

    # If summarize is requested, use AI to summarize results
    summary = None
    if summarize:
        search_context = f"Web search results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            search_context += f"{i}. **{r['title']}**\n"
            if r['snippet']:
                search_context += f"   {r['snippet']}\n"
            if r['link']:
                search_context += f"   Link: {r['link']}\n"
            search_context += "\n"

        # Get AI summary
        summary_conversation = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Summarize the following search results concisely and provide key insights. Include relevant links when appropriate."
            },
            {
                "role": "user",
                "content": search_context + "\n\nPlease summarize these search results and provide the most relevant information."
            }
        ]
        summary = generate_ai_response(summary_conversation)

    return jsonify({
        'results': results,
        'summary': summary,
        'query': query
    })

@app.route('/api/speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    audio_bytes = generate_speech(text)
    
    if audio_bytes:
        return audio_bytes, 200, {'Content-Type': 'audio/mpeg'}
    else:
        return jsonify({'error': 'Speech generation failed'}), 500

@app.route('/api/notes', methods=['GET', 'POST', 'DELETE'])
def notes():
    """Manage notes"""
    if request.method == 'GET':
        # Get from MongoDB
        if USE_MONGODB and db.is_connected():
            notes_list = db.get_all_notes()
            return jsonify(notes_list)
        return jsonify(user_data['notes'])

    elif request.method == 'POST':
        data = request.json
        title = data.get('title', 'Untitled')
        content = data.get('content', '')

        # Save to MongoDB
        if USE_MONGODB and db.is_connected():
            note = db.create_note(title=title, content=content)
            if note:
                return jsonify(note), 201

        # Fallback to in-memory
        note = {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': content,
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat()
        }
        user_data['notes'].append(note)
        return jsonify(note), 201

    elif request.method == 'DELETE':
        note_id = request.json.get('id')

        # Delete from MongoDB
        if USE_MONGODB and db.is_connected():
            db.delete_note(note_id)
            return jsonify({'status': 'success'})

        # Fallback to in-memory
        user_data['notes'] = [n for n in user_data['notes'] if n['id'] != note_id]
        return jsonify({'status': 'success'})

@app.route('/api/tasks', methods=['GET', 'POST', 'PUT', 'DELETE'])
def tasks():
    """Manage tasks"""
    if request.method == 'GET':
        # Get from MongoDB
        if USE_MONGODB and db.is_connected():
            tasks_list = db.get_all_tasks()
            return jsonify(tasks_list)
        return jsonify(user_data['tasks'])

    elif request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        priority = data.get('priority', 'medium')

        # Save to MongoDB
        if USE_MONGODB and db.is_connected():
            task = db.create_task(title=title, priority=priority)
            if task:
                return jsonify(task), 201

        # Fallback to in-memory
        task = {
            'id': str(uuid.uuid4()),
            'title': title,
            'completed': False,
            'priority': priority,
            'created': datetime.now().isoformat()
        }
        user_data['tasks'].append(task)
        return jsonify(task), 201

    elif request.method == 'PUT':
        task_id = request.json.get('id')

        # Update in MongoDB
        if USE_MONGODB and db.is_connected():
            updates = {}
            if 'completed' in request.json:
                updates['completed'] = request.json['completed']
            if 'title' in request.json:
                updates['title'] = request.json['title']
            if 'priority' in request.json:
                updates['priority'] = request.json['priority']

            task = db.update_task(task_id, updates)
            if task:
                return jsonify(task)
            return jsonify({'error': 'Task not found'}), 404

        # Fallback to in-memory
        for task in user_data['tasks']:
            if task['id'] == task_id:
                task['completed'] = request.json.get('completed', task['completed'])
                task['title'] = request.json.get('title', task['title'])
                task['priority'] = request.json.get('priority', task['priority'])
                return jsonify(task)
        return jsonify({'error': 'Task not found'}), 404

    elif request.method == 'DELETE':
        task_id = request.json.get('id')

        # Delete from MongoDB
        if USE_MONGODB and db.is_connected():
            db.delete_task(task_id)
            return jsonify({'status': 'success'})

        # Fallback to in-memory
        user_data['tasks'] = [t for t in user_data['tasks'] if t['id'] != task_id]
        return jsonify({'status': 'success'})

@app.route('/api/reminders', methods=['GET', 'POST', 'DELETE'])
def reminders():
    """Manage reminders"""
    if request.method == 'GET':
        # Get from MongoDB
        if USE_MONGODB and db.is_connected():
            reminders_list = db.get_all_reminders()
            return jsonify(reminders_list)
        return jsonify(user_data['reminders'])

    elif request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        reminder_datetime = data.get('datetime', '')

        # Save to MongoDB
        if USE_MONGODB and db.is_connected():
            reminder = db.create_reminder(title=title, reminder_datetime=reminder_datetime)
            if reminder:
                return jsonify(reminder), 201

        # Fallback to in-memory
        reminder = {
            'id': str(uuid.uuid4()),
            'title': title,
            'datetime': reminder_datetime,
            'created': datetime.now().isoformat()
        }
        user_data['reminders'].append(reminder)
        return jsonify(reminder), 201

    elif request.method == 'DELETE':
        reminder_id = request.json.get('id')

        # Delete from MongoDB
        if USE_MONGODB and db.is_connected():
            db.delete_reminder(reminder_id)
            return jsonify({'status': 'success'})

        # Fallback to in-memory
        user_data['reminders'] = [r for r in user_data['reminders'] if r['id'] != reminder_id]
        return jsonify({'status': 'success'})

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get user statistics"""
    # Get from MongoDB
    if USE_MONGODB and db.is_connected():
        db_stats = db.get_stats()
        db_stats['current_time'] = datetime.now().isoformat()
        return jsonify(db_stats)

    # Fallback to in-memory
    total_tasks = len(user_data['tasks'])
    completed_tasks = len([t for t in user_data['tasks'] if t['completed']])

    return jsonify({
        'total_notes': len(user_data['notes']),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': total_tasks - completed_tasks,
        'total_reminders': len(user_data['reminders']),
        'current_time': datetime.now().isoformat()
    })

# -------------------------------
# DocIQ Routes
# -------------------------------

@app.route('/api/dociq/upload', methods=['POST'])
def dociq_upload():
    """Upload and process document for DocIQ"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not supported. Use PDF, DOC, DOCX, or TXT.'}), 400

    try:
        # Secure the filename and save
        filename = secure_filename(file.filename)
        file_extension = get_file_extension(filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Extract text from document
        text = extract_text_from_document(file_path, file_extension)

        if text.startswith('Error'):
            # Clean up file on error
            os.remove(file_path)
            return jsonify({'error': text}), 500

        # Chunk the text for RAG
        chunks = chunk_text(text)

        # Store document info
        session_id = get_dociq_session_id()
        doc_id = str(uuid.uuid4())

        doc_info = {
            'id': doc_id,
            'name': filename,
            'original_name': file.filename,
            'extension': file_extension,
            'size': file_size,
            'path': file_path,
            'text_length': len(text),
            'chunks': chunks,
            'chunk_count': len(chunks),
            'uploaded_at': datetime.now().isoformat(),
            'status': 'ready'
        }

        # Save to MongoDB if connected
        if USE_MONGODB and db.is_connected():
            db.save_dociq_document(session_id, doc_info)
            print(f"[DocIQ Upload] Document saved to MongoDB: {filename}")
        else:
            # Fallback to in-memory
            session_data = get_dociq_documents()
            session_data['documents'].append(doc_info)

        # Debug logging
        print(f"[DocIQ Upload] Successfully added document: {filename}")
        print(f"[DocIQ Upload] Session ID: {session_id}")

        return jsonify({
            'success': True,
            'document': {
                'id': doc_id,
                'name': filename,
                'extension': file_extension,
                'size': file_size,
                'text_length': len(text),
                'chunk_count': len(chunks),
                'status': 'ready'
            }
        })

    except Exception as e:
        print(f"DocIQ upload error: {e}")
        return jsonify({'error': f'Failed to process document: {str(e)}'}), 500

@app.route('/api/dociq/documents', methods=['GET'])
def dociq_list_documents():
    """List all uploaded documents"""
    session_data = get_dociq_documents()

    documents = []
    for doc in session_data['documents']:
        documents.append({
            'id': doc['id'],
            'name': doc['name'],
            'extension': doc['extension'],
            'size': doc['size'],
            'text_length': doc.get('text_length', 0),
            'chunk_count': doc.get('chunk_count', 0),
            'uploaded_at': doc['uploaded_at'],
            'status': doc['status']
        })

    return jsonify({'documents': documents})

@app.route('/api/dociq/documents/<doc_id>', methods=['DELETE'])
def dociq_delete_document(doc_id):
    """Delete a specific document"""
    session_data = get_dociq_documents()

    for i, doc in enumerate(session_data['documents']):
        doc_doc_id = doc.get('doc_id') or doc.get('id')
        if doc_doc_id == doc_id:
            # Delete file from disk
            try:
                file_path = doc.get('path')
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

            # Delete from MongoDB
            if USE_MONGODB and db.is_connected():
                db.delete_dociq_document(doc_id)
            else:
                # Remove from in-memory list
                session_data['documents'].pop(i)

            return jsonify({'success': True, 'message': 'Document deleted'})

    return jsonify({'error': 'Document not found'}), 404

@app.route('/api/dociq/clear', methods=['POST'])
def dociq_clear():
    """Clear all documents and conversation"""
    session_id = get_dociq_session_id()
    session_data = get_dociq_documents()

    # Delete all files from disk
    for doc in session_data['documents']:
        try:
            file_path = doc.get('path')
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    # Clear from MongoDB
    if USE_MONGODB and db.is_connected():
        db.clear_dociq_documents(session_id)
        db.clear_dociq_conversation(session_id)
    else:
        # Clear in-memory data
        session_data['documents'] = []
        session_data['conversation'] = []

    return jsonify({'success': True, 'message': 'All documents cleared'})

@app.route('/api/dociq/chat', methods=['POST'])
def dociq_chat():
    """Chat with documents using RAG"""
    data = request.json
    user_message = data.get('message', '')
    session_id = get_dociq_session_id()

    print(f"[DocIQ Chat] Received message: {user_message[:50]}...")

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    session_data = get_dociq_documents()

    print(f"[DocIQ Chat] Documents found: {len(session_data['documents'])}")
    for doc in session_data['documents']:
        doc_name = doc.get('name', 'Unknown')
        chunk_count = doc.get('chunk_count', 0)
        print(f"[DocIQ Chat] - {doc_name}: {chunk_count} chunks")

    if not session_data['documents']:
        print("[DocIQ Chat] No documents found - returning error")
        return jsonify({
            'response': "Please upload some documents first. I need document content to provide accurate answers.",
            'has_documents': False
        })

    # Add user message to conversation history
    session_data['conversation'].append({
        'role': 'user',
        'content': user_message
    })

    # Save user message to MongoDB
    if USE_MONGODB and db.is_connected():
        db.save_dociq_conversation(session_id, 'user', user_message)

    # Generate response using RAG
    ai_response = generate_dociq_response(user_message, session_data)

    # Add AI response to conversation history
    session_data['conversation'].append({
        'role': 'assistant',
        'content': ai_response
    })

    # Save AI response to MongoDB
    if USE_MONGODB and db.is_connected():
        db.save_dociq_conversation(session_id, 'assistant', ai_response)

    return jsonify({
        'response': ai_response,
        'has_documents': True,
        'document_count': len(session_data['documents']),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/dociq/summary', methods=['GET'])
def dociq_summary():
    """Get summary of uploaded documents"""
    session_data = get_dociq_documents()

    if not session_data['documents']:
        return jsonify({'error': 'No documents uploaded'}), 400

    # Build document overview
    doc_overview = "**Uploaded Documents:**\n\n"
    total_text_length = 0

    for doc in session_data['documents']:
        doc_overview += f"- {doc['name']} ({doc['extension'].upper()}, {doc.get('text_length', 0)} chars)\n"
        total_text_length += doc.get('text_length', 0)

    # Generate summary using AI
    summary_prompt = f"""Please provide a brief summary of the following documents:

{doc_overview}

Combined document content preview:
{get_combined_document_context(session_data, max_context_length=4000)}

Provide:
1. A brief overview of what these documents contain
2. Key topics covered
3. Main takeaways"""

    summary_conversation = [
        {
            "role": "system",
            "content": "You are DocIQ, a document analysis assistant. Provide clear, concise summaries."
        },
        {
            "role": "user",
            "content": summary_prompt
        }
    ]

    summary = generate_ai_response(summary_conversation)

    return jsonify({
        'summary': summary,
        'document_count': len(session_data['documents']),
        'total_text_length': total_text_length
    })

# -------------------------------
# VizIQ Routes - Data Intelligence
# -------------------------------

def parse_csv_data(file_path):
    """Parse CSV file and return data"""
    import csv
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        for row in reader:
            data.append(row)
    return data, columns

def parse_excel_data(file_path):
    """Parse Excel file and return data"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active

        data = []
        columns = []

        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                columns = [str(cell) if cell else f'Column_{j}' for j, cell in enumerate(row)]
            else:
                row_data = {}
                for j, cell in enumerate(row):
                    col_name = columns[j] if j < len(columns) else f'Column_{j}'
                    row_data[col_name] = cell
                data.append(row_data)

        return data, columns
    except ImportError:
        return None, "Error: openpyxl library not installed"

def parse_json_data(file_path):
    """Parse JSON file and return data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Handle different JSON structures
    if isinstance(raw_data, list):
        data = raw_data
        if data and isinstance(data[0], dict):
            columns = list(data[0].keys())
        else:
            columns = ['value']
            data = [{'value': item} for item in raw_data]
    elif isinstance(raw_data, dict):
        # Check if it's a records-style dict
        if all(isinstance(v, list) for v in raw_data.values()):
            columns = list(raw_data.keys())
            max_len = max(len(v) for v in raw_data.values())
            data = []
            for i in range(max_len):
                row = {}
                for col in columns:
                    row[col] = raw_data[col][i] if i < len(raw_data[col]) else None
                data.append(row)
        else:
            data = [raw_data]
            columns = list(raw_data.keys())
    else:
        data = [{'value': raw_data}]
        columns = ['value']

    return data, columns

def detect_column_types(data, columns):
    """Detect data types for each column"""
    dtypes = {}

    for col in columns:
        values = [row.get(col) for row in data[:100] if row.get(col) is not None]

        if not values:
            dtypes[col] = 'unknown'
            continue

        # Try to detect type
        numeric_count = 0
        date_count = 0

        for val in values:
            if isinstance(val, (int, float)):
                numeric_count += 1
            elif isinstance(val, str):
                try:
                    float(val.replace(',', '').replace('$', '').replace('%', ''))
                    numeric_count += 1
                except:
                    # Check for date patterns
                    if any(sep in val for sep in ['-', '/', '.']):
                        date_count += 1

        if numeric_count > len(values) * 0.7:
            dtypes[col] = 'numeric'
        elif date_count > len(values) * 0.5:
            dtypes[col] = 'date'
        else:
            dtypes[col] = 'categorical'

    return dtypes

def clean_numeric_value(val):
    """Clean and convert value to numeric"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            cleaned = val.replace(',', '').replace('$', '').replace('%', '').strip()
            return float(cleaned)
        except:
            return None
    return None

def calculate_statistics(data, columns, dtypes):
    """Calculate statistics for numeric columns"""
    stats = {}

    for col in columns:
        if dtypes.get(col) == 'numeric':
            values = [clean_numeric_value(row.get(col)) for row in data]
            values = [v for v in values if v is not None]

            if values:
                stats[col] = {
                    'min': min(values),
                    'max': max(values),
                    'sum': sum(values),
                    'mean': sum(values) / len(values),
                    'count': len(values)
                }

                # Calculate median
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                if n % 2 == 0:
                    stats[col]['median'] = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
                else:
                    stats[col]['median'] = sorted_vals[n//2]

    return stats

def generate_kpis(data, columns, dtypes, stats, filename):
    """Generate KPIs from data"""
    kpis = []

    # Total rows KPI
    kpis.append({
        'label': 'Total Records',
        'value': len(data),
        'icon': 'database',
        'description': f'Total rows in {filename}'
    })

    # Find numeric columns and create KPIs
    for col in columns[:6]:  # Limit to first 6 columns
        if col in stats:
            s = stats[col]
            kpis.append({
                'label': f'Total {col}',
                'value': round(s['sum'], 2),
                'icon': 'trending-up',
                'description': f"Sum of all {col} values",
                'change': None
            })
            kpis.append({
                'label': f'Avg {col}',
                'value': round(s['mean'], 2),
                'icon': 'bar-chart',
                'description': f"Average {col}",
                'change': None
            })
            break  # Just one numeric column for now

    # Count unique values for categorical columns
    for col in columns:
        if dtypes.get(col) == 'categorical':
            unique_vals = set(row.get(col) for row in data if row.get(col))
            kpis.append({
                'label': f'Unique {col}',
                'value': len(unique_vals),
                'icon': 'layers',
                'description': f'Distinct values in {col}'
            })
            break  # Just one categorical column

    return kpis[:6]  # Return max 6 KPIs

def generate_chart_configs(data, columns, dtypes, stats):
    """Generate chart configurations based on data - 3 charts in first row, 1 trend chart in second row"""
    charts = []

    numeric_cols = [c for c in columns if dtypes.get(c) == 'numeric']
    categorical_cols = [c for c in columns if dtypes.get(c) == 'categorical']

    # ============ ROW 1: Column Chart, Distribution Chart, Comparison Chart ============

    # 1. COLUMN CHART - Bar chart for categorical data with numeric values
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]

        # Aggregate data by category
        aggregated = {}
        for row in data:
            cat_val = str(row.get(cat_col, 'Unknown'))
            num_val = clean_numeric_value(row.get(num_col))
            if num_val is not None:
                if cat_val not in aggregated:
                    aggregated[cat_val] = 0
                aggregated[cat_val] += num_val

        # Sort and limit to top 8
        sorted_items = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:8]

        if sorted_items:
            charts.append({
                'id': 'column-chart',
                'type': 'bar',
                'title': f'Column: {num_col} by {cat_col}',
                'labels': [item[0][:12] for item in sorted_items],  # Truncate labels
                'data': [round(item[1], 2) for item in sorted_items],
                'insight': f"Top: {sorted_items[0][0]} ({round(sorted_items[0][1], 2)})"
            })

    # 2. DISTRIBUTION CHART - Doughnut/Pie chart for categorical distribution
    if categorical_cols:
        cat_col = categorical_cols[0] if len(categorical_cols) == 1 else categorical_cols[1] if len(categorical_cols) > 1 else categorical_cols[0]
        counts = {}
        for row in data:
            val = str(row.get(cat_col, 'Unknown'))
            counts[val] = counts.get(val, 0) + 1

        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:6]

        if sorted_counts:
            total = sum(item[1] for item in sorted_counts)
            charts.append({
                'id': 'distribution-chart',
                'type': 'doughnut',
                'title': f'Distribution: {cat_col}',
                'labels': [item[0][:15] for item in sorted_counts],
                'data': [item[1] for item in sorted_counts],
                'insight': f"Largest: {sorted_counts[0][0]} ({round(sorted_counts[0][1]/total*100, 1)}%)"
            })

    # 3. COMPARISON CHART - Compare multiple numeric columns
    if numeric_cols and len(numeric_cols) >= 2:
        col1, col2 = numeric_cols[0], numeric_cols[1]

        if col1 in stats and col2 in stats:
            charts.append({
                'id': 'comparison-chart',
                'type': 'bar',
                'title': f'Comparison: Metrics',
                'labels': ['Average', 'Maximum', 'Minimum'],
                'datasets': [
                    {
                        'label': col1[:15],
                        'data': [round(stats[col1]['mean'], 2), round(stats[col1]['max'], 2), round(stats[col1]['min'], 2)]
                    },
                    {
                        'label': col2[:15],
                        'data': [round(stats[col2]['mean'], 2), round(stats[col2]['max'], 2), round(stats[col2]['min'], 2)]
                    }
                ],
                'insight': f"Comparing {col1} vs {col2} metrics"
            })
    elif numeric_cols and len(numeric_cols) == 1:
        # Single numeric column - show stats as bar chart
        col = numeric_cols[0]
        if col in stats:
            charts.append({
                'id': 'comparison-chart',
                'type': 'bar',
                'title': f'Statistics: {col}',
                'labels': ['Average', 'Maximum', 'Minimum'],
                'data': [round(stats[col]['mean'], 2), round(stats[col]['max'], 2), round(stats[col]['min'], 2)],
                'insight': f"Range: {round(stats[col]['min'], 2)} to {round(stats[col]['max'], 2)}"
            })

    # ============ ROW 2: Trend Chart (Full Width) ============

    # 4. TREND CHART - Line chart for time series or sequential data
    if numeric_cols and len(data) > 5:
        num_col = numeric_cols[0]
        values = []
        labels = []

        # Check for date column
        date_cols = [c for c in columns if dtypes.get(c) == 'date']

        for i, row in enumerate(data[:30]):  # Limit to 30 points for clarity
            val = clean_numeric_value(row.get(num_col))
            if val is not None:
                values.append(val)
                if date_cols:
                    labels.append(str(row.get(date_cols[0], i+1))[:10])
                else:
                    labels.append(f'P{i+1}')

        if values and len(values) >= 3:
            # Calculate trend direction
            avg_first_half = sum(values[:len(values)//2]) / (len(values)//2) if len(values) >= 2 else 0
            avg_second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2) if len(values) >= 2 else 0
            trend = "Upward" if avg_second_half > avg_first_half else "Downward" if avg_second_half < avg_first_half else "Stable"

            charts.append({
                'id': 'trend-chart',
                'type': 'line',
                'title': f'Trend Analysis: {num_col}',
                'labels': labels,
                'data': [round(v, 2) for v in values],
                'insight': f"{trend} trend detected. Range: {round(min(values), 2)} - {round(max(values), 2)}"
            })

    # Ensure we have at least some charts
    if len(charts) < 3 and numeric_cols:
        # Add a simple bar chart if we don't have enough
        col = numeric_cols[0]
        if col in stats and 'column-chart' not in [c['id'] for c in charts]:
            values = []
            for row in data[:10]:
                val = clean_numeric_value(row.get(col))
                if val is not None:
                    values.append(val)
            if values:
                charts.insert(0, {
                    'id': 'column-chart',
                    'type': 'bar',
                    'title': f'Values: {col}',
                    'labels': [f'Row {i+1}' for i in range(len(values))],
                    'data': [round(v, 2) for v in values],
                    'insight': f"Showing first {len(values)} values"
                })

    return charts

def generate_insights(data, columns, dtypes, stats, filename):
    """Generate AI insights from data"""
    insights = []

    # Data quality insight
    null_counts = {}
    for col in columns:
        null_count = sum(1 for row in data if row.get(col) is None or row.get(col) == '')
        if null_count > 0:
            null_counts[col] = null_count

    if null_counts:
        most_nulls = max(null_counts.items(), key=lambda x: x[1])
        insights.append({
            'icon': '⚠️',
            'type': 'warning',
            'title': 'Data Quality Alert',
            'description': f"'{most_nulls[0]}' has {most_nulls[1]} missing values ({round(most_nulls[1]/len(data)*100, 1)}% of data)"
        })

    # Numeric insights
    for col in columns:
        if col in stats:
            s = stats[col]

            # High variance insight
            if s['max'] > s['mean'] * 5:
                insights.append({
                    'icon': '📈',
                    'type': 'trend-up',
                    'title': f'High Variance in {col}',
                    'description': f"Maximum value ({round(s['max'], 2)}) is significantly higher than average ({round(s['mean'], 2)})"
                })

            # Summary insight
            insights.append({
                'icon': '📊',
                'type': 'info',
                'title': f'{col} Summary',
                'description': f"Total: {round(s['sum'], 2)}, Average: {round(s['mean'], 2)}, Median: {round(s['median'], 2)}"
            })
            break

    # Categorical insights
    for col in columns:
        if dtypes.get(col) == 'categorical':
            counts = {}
            for row in data:
                val = row.get(col)
                if val:
                    counts[str(val)] = counts.get(str(val), 0) + 1

            if counts:
                top_item = max(counts.items(), key=lambda x: x[1])
                insights.append({
                    'icon': '🏆',
                    'type': 'trend-up',
                    'title': f'Top {col}',
                    'description': f"'{top_item[0]}' is most frequent with {top_item[1]} occurrences ({round(top_item[1]/len(data)*100, 1)}%)"
                })
            break

    # Row count insight
    insights.append({
        'icon': '📁',
        'type': 'info',
        'title': 'Dataset Size',
        'description': f"Your dataset contains {len(data)} records across {len(columns)} columns"
    })

    return insights[:6]

def generate_dashboard_name(filename, columns):
    """Generate a smart dashboard name"""
    base_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()

    # Try to identify domain from column names
    col_text = ' '.join(columns).lower()

    if any(word in col_text for word in ['sale', 'revenue', 'price', 'amount', 'cost']):
        return f"{base_name} - Sales Analytics"
    elif any(word in col_text for word in ['employee', 'salary', 'department', 'hr']):
        return f"{base_name} - HR Analytics"
    elif any(word in col_text for word in ['customer', 'user', 'client']):
        return f"{base_name} - Customer Analytics"
    elif any(word in col_text for word in ['product', 'inventory', 'stock']):
        return f"{base_name} - Product Analytics"
    elif any(word in col_text for word in ['date', 'time', 'month', 'year']):
        return f"{base_name} - Time Series Analysis"
    else:
        return f"{base_name} Dashboard"

@app.route('/api/viziq/upload', methods=['POST'])
def viziq_upload():
    """Upload and process data file for VizIQ"""
    global viziq_storage

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if file_extension not in ['csv', 'xlsx', 'xls', 'json']:
        return jsonify({'error': 'Unsupported file type. Use CSV, XLSX, or JSON.'}), 400

    try:
        # Save file temporarily
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"viziq_{uuid.uuid4()}_{filename}")
        file.save(file_path)

        # Parse file based on type
        if file_extension == 'csv':
            data, columns = parse_csv_data(file_path)
        elif file_extension in ['xlsx', 'xls']:
            data, columns = parse_excel_data(file_path)
            if data is None:
                return jsonify({'error': columns}), 500
        elif file_extension == 'json':
            data, columns = parse_json_data(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        # Clean up temp file
        os.remove(file_path)

        if not data:
            return jsonify({'error': 'No data found in file'}), 400

        # Detect column types
        dtypes = detect_column_types(data, columns)

        # Calculate statistics
        stats = calculate_statistics(data, columns, dtypes)

        # Generate dashboard name
        dashboard_name = generate_dashboard_name(filename, columns)

        # Generate KPIs
        kpis = generate_kpis(data, columns, dtypes, stats, filename)

        # Generate chart configurations
        charts = generate_chart_configs(data, columns, dtypes, stats)

        # Generate insights
        insights = generate_insights(data, columns, dtypes, stats, filename)

        # Store data in memory for immediate use
        viziq_storage = {
            'data': data,
            'columns': columns,
            'dtypes': dtypes,
            'stats': stats,
            'filename': filename
        }

        # Prepare preview data (first 100 rows)
        preview_data = data[:100]

        # Save to MongoDB for persistence
        if USE_MONGODB and db.is_connected():
            session_id = get_session_id()
            viziq_data_info = {
                'filename': filename,
                'columns': columns,
                'dtypes': dtypes,
                'stats': stats,
                'row_count': len(data),
                'kpis': kpis,
                'charts': charts,
                'insights': insights,
                'preview_data': preview_data,
                'dashboard_name': dashboard_name
            }
            db.save_viziq_data(session_id, viziq_data_info)
            print(f"[VizIQ] Data saved to MongoDB: {filename}")

        return jsonify({
            'success': True,
            'dashboard_name': dashboard_name,
            'description': f'AI-generated analytics from {filename}',
            'rows': len(data),
            'cols': len(columns),
            'columns': columns,
            'dtypes': dtypes,
            'kpis': kpis,
            'charts': charts,
            'insights': insights,
            'preview': preview_data
        })

    except Exception as e:
        print(f"VizIQ upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500

@app.route('/api/viziq/clear', methods=['POST'])
def viziq_clear():
    """Clear VizIQ data"""
    global viziq_storage

    # Clear from MongoDB
    if USE_MONGODB and db.is_connected():
        session_id = get_session_id()
        db.clear_viziq_data(session_id)

    # Clear in-memory storage
    viziq_storage = {
        'data': None,
        'columns': [],
        'dtypes': {},
        'filename': '',
        'analysis': None
    }
    return jsonify({'success': True})

@app.route('/api/viziq/data', methods=['GET'])
def viziq_get_data():
    """Get current VizIQ data"""
    # Try to get from in-memory first
    if viziq_storage['data'] is not None:
        return jsonify({
            'filename': viziq_storage['filename'],
            'columns': viziq_storage['columns'],
            'dtypes': viziq_storage['dtypes'],
            'rows': len(viziq_storage['data']),
            'preview': viziq_storage['data'][:50]
        })

    # Try to get from MongoDB
    if USE_MONGODB and db.is_connected():
        session_id = get_session_id()
        viziq_data = db.get_viziq_data(session_id)
        if viziq_data:
            return jsonify({
                'filename': viziq_data.get('filename'),
                'columns': viziq_data.get('columns', []),
                'dtypes': viziq_data.get('dtypes', {}),
                'rows': viziq_data.get('row_count', 0),
                'preview': viziq_data.get('preview_data', [])[:50],
                'kpis': viziq_data.get('kpis', []),
                'charts': viziq_data.get('charts', []),
                'insights': viziq_data.get('insights', []),
                'dashboard_name': viziq_data.get('dashboard_name')
            })

    return jsonify({'error': 'No data loaded'}), 404

# -------------------------------
# Main
# -------------------------------

if __name__ == '__main__':
    print("=" * 50)
    print("Axio AI Code Assistant by Perfionix AI - Starting...")
    print("=" * 50)
    print(f"GPT Server: {GPT_SERVER_URL}")
    print(f"GPT Model: {GPT_MODEL}")
    print(f"Gemini Model: {GEMINI_MODEL}")
    print(f"Gemini Client: {'Initialized' if gemini_client else 'Not initialized'}")
    print(f"Voice: {'Enabled' if ELEVENLABS_API_KEY else 'Disabled (no API key)'}")
    print(f"MongoDB: {'Connected' if USE_MONGODB and db.is_connected() else 'Not connected (using in-memory storage)'}")
    print("=" * 50)
    print("Open http://localhost:5000 in your browser")
    print("=" * 50)

    app.run(debug=os.getenv('FLASK_DEBUG', 'True') == 'True', host='0.0.0.0', port=5000)
