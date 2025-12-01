from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime, timedelta
from io import BytesIO
import threading
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# -------------------------------
# Configuration
# -------------------------------

GPT_SERVER_URL = os.getenv('GPT_SERVER_URL', 'http://localhost:11434/api/chat')
GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-oss:120b-cloud')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_ID = os.getenv('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')

# In-memory storage (replace with database in production)
user_data = {
    'notes': [],
    'reminders': [],
    'tasks': []
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


def get_conversation():
    """Get or initialize conversation for current session"""
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
    """Save conversation to session and mark as modified"""
    session['conversation'] = conversation
    session.modified = True

def generate_ai_response(conversation):
    """Generate AI response from conversation history"""
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

def web_search(query):
    """Perform web search - tries multiple methods"""
    print(f"🔍 Starting web search for: {query}")

    # Method 1: Try googlesearch-python library
    results = web_search_googlesearch(query)
    if results:
        print(f"✅ googlesearch-python returned {len(results)} results")
        return results

    # Method 2: Try DuckDuckGo
    results = web_search_duckduckgo(query)
    if results:
        print(f"✅ DuckDuckGo returned {len(results)} results")
        return results

    # Method 3: Fallback to direct Google scraping
    results = web_search_google_scrape(query)
    if results:
        print(f"✅ Google scrape returned {len(results)} results")
        return results

    print("❌ All search methods failed")
    return []


def web_search_googlesearch(query):
    """Search using googlesearch-python library"""
    try:
        from googlesearch import search
        results = []
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


def web_search_duckduckgo(query):
    """Search using DuckDuckGo HTML"""
    import urllib.parse

    try:
        search_url = "https://html.duckduckgo.com/html/"
        data = {'q': query}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        response = requests.post(search_url, data=data, headers=headers, timeout=10)
        response.raise_for_status()

        from bs4 import BeautifulSoup
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

                if title and link:
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'link': link
                    })

        return results if results else None
    except Exception as e:
        print(f"DuckDuckGo error: {e}")
        return None


def web_search_google_scrape(query):
    """Fallback web search using direct Google scraping"""
    import urllib.parse
    from bs4 import BeautifulSoup

    search_url = "https://www.google.com/search"
    params = {
        'q': query,
        'num': 10,
        'hl': 'en'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Find all search result divs
        search_divs = soup.find_all('div', class_='g')

        for div in search_divs[:5]:
            try:
                # Get title
                title_elem = div.find('h3')
                title = title_elem.get_text() if title_elem else ''

                # Get link
                link_elem = div.find('a')
                link = link_elem.get('href', '') if link_elem else ''

                # Clean the link
                if link.startswith('/url?q='):
                    link = link.split('/url?q=')[1].split('&')[0]
                    link = urllib.parse.unquote(link)

                # Get snippet
                snippet_elem = div.find('div', class_='VwiC3b') or div.find('span', class_='aCOpRe')
                snippet = snippet_elem.get_text() if snippet_elem else ''

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
# Routes
# -------------------------------

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')
    force_search = data.get('search', False)

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    ai_response, user_idx, ai_idx, searched = chat_with_ai(user_message, force_search)

    return jsonify({
        'response': ai_response,
        'user_index': user_idx,
        'ai_index': ai_idx,
        'searched': searched,
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
        return jsonify(user_data['notes'])
    
    elif request.method == 'POST':
        data = request.json
        note = {
            'id': str(uuid.uuid4()),
            'title': data.get('title', 'Untitled'),
            'content': data.get('content', ''),
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat()
        }
        user_data['notes'].append(note)
        return jsonify(note), 201
    
    elif request.method == 'DELETE':
        note_id = request.json.get('id')
        user_data['notes'] = [n for n in user_data['notes'] if n['id'] != note_id]
        return jsonify({'status': 'success'})

@app.route('/api/tasks', methods=['GET', 'POST', 'PUT', 'DELETE'])
def tasks():
    """Manage tasks"""
    if request.method == 'GET':
        return jsonify(user_data['tasks'])
    
    elif request.method == 'POST':
        data = request.json
        task = {
            'id': str(uuid.uuid4()),
            'title': data.get('title', ''),
            'completed': False,
            'priority': data.get('priority', 'medium'),
            'created': datetime.now().isoformat()
        }
        user_data['tasks'].append(task)
        return jsonify(task), 201
    
    elif request.method == 'PUT':
        task_id = request.json.get('id')
        for task in user_data['tasks']:
            if task['id'] == task_id:
                task['completed'] = request.json.get('completed', task['completed'])
                task['title'] = request.json.get('title', task['title'])
                task['priority'] = request.json.get('priority', task['priority'])
                return jsonify(task)
        return jsonify({'error': 'Task not found'}), 404
    
    elif request.method == 'DELETE':
        task_id = request.json.get('id')
        user_data['tasks'] = [t for t in user_data['tasks'] if t['id'] != task_id]
        return jsonify({'status': 'success'})

@app.route('/api/reminders', methods=['GET', 'POST', 'DELETE'])
def reminders():
    """Manage reminders"""
    if request.method == 'GET':
        return jsonify(user_data['reminders'])
    
    elif request.method == 'POST':
        data = request.json
        reminder = {
            'id': str(uuid.uuid4()),
            'title': data.get('title', ''),
            'datetime': data.get('datetime', ''),
            'created': datetime.now().isoformat()
        }
        user_data['reminders'].append(reminder)
        return jsonify(reminder), 201
    
    elif request.method == 'DELETE':
        reminder_id = request.json.get('id')
        user_data['reminders'] = [r for r in user_data['reminders'] if r['id'] != reminder_id]
        return jsonify({'status': 'success'})

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get user statistics"""
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
# Main
# -------------------------------

if __name__ == '__main__':
    print("🚀 Axio AI Code Assistant by Perfionix AI - Starting...")
    print(f"📡 GPT Server: {GPT_SERVER_URL}")
    print(f"🤖 Model: {GPT_MODEL}")
    print(f"🎤 Voice: {'Enabled' if ELEVENLABS_API_KEY else 'Disabled (no API key)'}")
    print("\n✨ Open http://localhost:5000 in your browser\n")
    
    app.run(debug=os.getenv('FLASK_DEBUG', 'True') == 'True', host='0.0.0.0', port=5000)
