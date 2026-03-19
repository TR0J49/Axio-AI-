"""
AI Service - Handles AI response generation via Azure OpenAI
"""
import json
from datetime import datetime
from openai import AzureOpenAI

from app.config.settings import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT,
    DEFAULT_AI_MODEL
)
from app.config.constants import AI_MODELS

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)


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
- Cite sources inline naturally (e.g. "According to Apple.com..." or "Source: BBC Weather")
- NEVER use footnote-style citations like [^1^], [^2^], [1], [2], or similar reference markers
- Summarize key findings clearly
- Provide links when relevant using markdown: [text](url)

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

FOLLOW-UP SUGGESTIONS (REQUIRED):
At the very end of EVERY response, you MUST append exactly 3 short follow-up suggestion questions the user might ask next.
Format them EXACTLY like this (no extra spaces or newlines inside the block):
<<<SUGGESTIONS>>>suggestion 1|||suggestion 2|||suggestion 3<<<END_SUGGESTIONS>>>
Rules:
- Each suggestion must be under 60 characters
- Make them contextual and relevant to your response
- Use natural question or action phrasing (e.g. "How do I optimize this?" or "Show me an example")
- Do NOT place <<<SUGGESTIONS>>> or <<<END_SUGGESTIONS>>> anywhere else in your response
- The suggestion block must be the very last thing in your response

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""


def get_current_model(session: dict):
    """Get the current AI model from session"""
    if 'ai_model' not in session:
        session['ai_model'] = DEFAULT_AI_MODEL
    return session['ai_model']


def set_current_model(session: dict, model: str):
    """Set the current AI model in session"""
    if model in AI_MODELS and AI_MODELS[model]['available']:
        session['ai_model'] = model
        return True
    return False


def generate_azure_response(conversation, model_label="Core"):
    """Generate AI response using Azure OpenAI"""
    try:
        print(f"[Laplacian {model_label}] Using Azure OpenAI deployment: {AZURE_OPENAI_DEPLOYMENT}")
        print(f"[Laplacian {model_label}] Sending request to Azure OpenAI...")

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=conversation,
            max_completion_tokens=32768,
            temperature=1.0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        content = response.choices[0].message.content
        print(f"[Laplacian {model_label}] Response received: {len(content)} characters")
        return content

    except Exception as e:
        error_msg = str(e)
        print(f"[Laplacian {model_label}] Error: {error_msg}")

        if "401" in error_msg or "Unauthorized" in error_msg:
            return "Authentication error: Invalid Azure OpenAI API key. Please check your AZURE_OPENAI_API_KEY in .env"
        elif "404" in error_msg or "DeploymentNotFound" in error_msg:
            return f"Deployment '{AZURE_OPENAI_DEPLOYMENT}' not found. Please verify your AZURE_OPENAI_DEPLOYMENT in .env"
        elif "429" in error_msg:
            return "Rate limit exceeded. Please wait a moment and try again."
        elif "timeout" in error_msg.lower():
            return "Request timed out. The model is taking too long to respond. Please try again."
        else:
            return f"Azure OpenAI error: {error_msg}"


def generate_ai_response(conversation, model=None, session: dict = None):
    """Generate AI response from conversation history using selected model"""
    current_model = model or (get_current_model(session) if session else DEFAULT_AI_MODEL)

    # Map model IDs to labels for logging
    label_map = {
        'gpt': 'Core',
        'gemini': 'Lite',
        'coder': 'Coder',
        'max': 'Max'
    }
    label = label_map.get(current_model, 'Core')

    # All models use the same Azure OpenAI backend
    return generate_azure_response(conversation, model_label=label)
