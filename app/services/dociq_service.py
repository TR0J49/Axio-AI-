"""
DocIQ Service - Document Intelligence and RAG functionality
"""
import os
import uuid
from datetime import datetime, timezone


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'

from app.config.settings import USE_MONGODB, DOCIQ_MODEL
from app.services.ai_service import generate_ai_response
from app.utils.text_processing import extract_text_from_document, chunk_text
from app.utils.file_helpers import secure_filename


# Fallback in-memory storage keyed by session_id to isolate users
_dociq_storage: dict[str, dict] = {}


def _get_fallback_storage(session_id: str) -> dict:
    if session_id not in _dociq_storage:
        _dociq_storage[session_id] = {'documents': [], 'conversation': []}
    return _dociq_storage[session_id]


def get_dociq_session_id(session: dict):
    """Get or create DocIQ session ID"""
    if 'dociq_session_id' not in session:
        session['dociq_session_id'] = str(uuid.uuid4())
        print(f"[DocIQ] Created new session ID: {session['dociq_session_id']}")
    return session['dociq_session_id']


def get_dociq_documents(session: dict):
    """Get documents for current session - uses MongoDB or fallback storage"""
    from database import get_database
    db = get_database()
    session_id = get_dociq_session_id(session)

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

    # Fallback to per-session in-memory storage
    storage = _get_fallback_storage(session_id)
    doc_count = len(storage['documents'])
    print(f"[DocIQ] Using in-memory storage for session {session_id[:8]} with {doc_count} documents")
    return storage


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
    """Generate AI response based on document context with structured output"""
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

CRITICAL OUTPUT FORMAT RULES:
You MUST always respond in STRUCTURED FORMAT - NEVER write long paragraphs.

FORMAT YOUR RESPONSES AS:

## Summary
- One line summary of the answer

## Key Points
- Point 1
- Point 2
- Point 3

## Details
| Aspect | Information |
|--------|-------------|
| Item 1 | Details |
| Item 2 | Details |

## Visual Diagram (when applicable)
```mermaid
graph TD
    A["Topic"] --> B["Subtopic 1"]
    A --> C["Subtopic 2"]
```

IMPORTANT GUIDELINES:
- ALWAYS use bullet points (-)
- ALWAYS use tables for comparisons
- ALWAYS include a Mermaid diagram for processes, flows, or relationships
- Keep each point SHORT and CONCISE
- Use headers (##) to organize sections
- Quote relevant passages with > blockquote
- Cite which document the information comes from
- If information is not in documents, clearly state that

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

    # Use gpt-oss:20b-cloud for DocIQ - structured responses
    print(f"[DocIQ] Using {DOCIQ_MODEL} for structured document analysis")
    return generate_ai_response(conversation)


def process_document_upload(file_bytes: bytes, original_filename: str, upload_folder: str, session: dict):
    """Process uploaded document and return document info"""
    from database import get_database
    db = get_database()

    filename = secure_filename(original_filename)
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(upload_folder, unique_filename)

    # Write file to disk
    with open(file_path, 'wb') as f:
        f.write(file_bytes)

    # Get file size
    file_size = os.path.getsize(file_path)

    # Extract text from document
    text = extract_text_from_document(file_path, file_extension)

    if text.startswith('Error'):
        # Clean up file on error
        os.remove(file_path)
        return None, text

    # Chunk the text for RAG
    chunks = chunk_text(text)

    # Store document info
    session_id = get_dociq_session_id(session)
    doc_id = str(uuid.uuid4())

    doc_info = {
        'id': doc_id,
        'name': filename,
        'original_name': original_filename,
        'extension': file_extension,
        'size': file_size,
        'path': file_path,
        'text_length': len(text),
        'chunks': chunks,
        'chunk_count': len(chunks),
        'uploaded_at': _utcnow_iso(),
        'status': 'ready'
    }

    # Save to MongoDB if connected
    if USE_MONGODB and db.is_connected():
        db.save_dociq_document(session_id, doc_info)
        print(f"[DocIQ Upload] Document saved to MongoDB: {filename}")
    else:
        # Fallback to in-memory
        session_data = get_dociq_documents(session)
        session_data['documents'].append(doc_info)

    print(f"[DocIQ Upload] Successfully added document: {filename}")
    print(f"[DocIQ Upload] Session ID: {session_id}")

    return doc_info, None


def delete_document(session: dict, doc_id):
    """Delete a specific document"""
    from database import get_database
    db = get_database()
    session_data = get_dociq_documents(session)

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

            return True

    return False


def clear_all_documents(session: dict):
    """Clear all documents and conversation"""
    from database import get_database
    db = get_database()
    session_id = get_dociq_session_id(session)
    session_data = get_dociq_documents(session)

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


def save_chat_message(session: dict, role, content):
    """Save a chat message to the conversation"""
    from database import get_database
    db = get_database()
    session_id = get_dociq_session_id(session)
    session_data = get_dociq_documents(session)

    # Add to conversation history
    session_data['conversation'].append({
        'role': role,
        'content': content
    })

    # Save to MongoDB
    if USE_MONGODB and db.is_connected():
        db.save_dociq_conversation(session_id, role, content)


def generate_summary(session: dict):
    """Generate structured summary of uploaded documents"""
    session_data = get_dociq_documents(session)

    if not session_data['documents']:
        return None, "No documents uploaded"

    # Build document overview
    doc_overview = "**Uploaded Documents:**\n\n"
    total_text_length = 0

    for doc in session_data['documents']:
        doc_overview += f"- {doc['name']} ({doc['extension'].upper()}, {doc.get('text_length', 0)} chars)\n"
        total_text_length += doc.get('text_length', 0)

    # Generate summary using AI
    summary_prompt = f"""Analyze and summarize the following documents in STRUCTURED FORMAT:

{doc_overview}

Document content:
{get_combined_document_context(session_data, max_context_length=6000)}

YOU MUST respond in this EXACT structure:

## Overview
- One line describing what these documents are about

## Document List
| Document | Type | Key Content |
|----------|------|-------------|
| name | type | brief description |

## Key Topics
- Topic 1
- Topic 2
- Topic 3

## Important Information
- Key fact 1
- Key fact 2
- Key data point

## Document Structure
```mermaid
graph TD
    A["Documents"] --> B["Document 1"]
    A --> C["Document 2"]
    B --> D["Key Topics"]
    C --> E["Key Topics"]
```

## Takeaways
- Main conclusion 1
- Main conclusion 2"""

    summary_conversation = [
        {
            "role": "system",
            "content": """You are DocIQ, a document analysis assistant by Perfionix AI.

CRITICAL: You MUST respond in STRUCTURED FORMAT only.
- Use bullet points (-) for all lists
- Use tables for comparisons
- Include Mermaid diagrams for structure visualization
- NO long paragraphs - only short, concise points
- Use ## headers to organize sections"""
        },
        {
            "role": "user",
            "content": summary_prompt
        }
    ]

    # Use gpt-oss:20b-cloud for structured summarization
    print(f"[DocIQ Summary] Using {DOCIQ_MODEL} for structured summary")
    summary = generate_ai_response(summary_conversation)

    return {
        'summary': summary,
        'document_count': len(session_data['documents']),
        'total_text_length': total_text_length
    }, None
