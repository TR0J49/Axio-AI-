"""
DocIQ routes - Document Intelligence endpoints
"""
import os
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

from app.config.settings import USE_MONGODB
from app.utils.file_helpers import allowed_file
from app.services.dociq_service import (
    get_dociq_documents, get_dociq_session_id,
    process_document_upload, delete_document, clear_all_documents,
    generate_dociq_response, save_chat_message, generate_summary
)

dociq_bp = Blueprint('dociq', __name__)


@dociq_bp.route('/upload', methods=['POST'])
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
        doc_info, error = process_document_upload(file, current_app.config['UPLOAD_FOLDER'])

        if error:
            return jsonify({'error': error}), 500

        return jsonify({
            'success': True,
            'document': {
                'id': doc_info['id'],
                'name': doc_info['name'],
                'extension': doc_info['extension'],
                'size': doc_info['size'],
                'text_length': doc_info['text_length'],
                'chunk_count': doc_info['chunk_count'],
                'status': doc_info['status']
            }
        })

    except Exception as e:
        print(f"DocIQ upload error: {e}")
        return jsonify({'error': f'Failed to process document: {str(e)}'}), 500


@dociq_bp.route('/documents', methods=['GET'])
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


@dociq_bp.route('/documents/<doc_id>', methods=['DELETE'])
def dociq_delete_document(doc_id):
    """Delete a specific document"""
    if delete_document(doc_id):
        return jsonify({'success': True, 'message': 'Document deleted'})
    return jsonify({'error': 'Document not found'}), 404


@dociq_bp.route('/clear', methods=['POST'])
def dociq_clear():
    """Clear all documents and conversation"""
    clear_all_documents()
    return jsonify({'success': True, 'message': 'All documents cleared'})


@dociq_bp.route('/chat', methods=['POST'])
def dociq_chat():
    """Chat with documents using RAG"""
    data = request.json
    user_message = data.get('message', '')

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

    # Save user message
    save_chat_message('user', user_message)

    # Generate response using RAG
    ai_response = generate_dociq_response(user_message, session_data)

    # Save AI response
    save_chat_message('assistant', ai_response)

    return jsonify({
        'response': ai_response,
        'has_documents': True,
        'document_count': len(session_data['documents']),
        'timestamp': datetime.now().isoformat()
    })


@dociq_bp.route('/summary', methods=['GET'])
def dociq_summary():
    """Get structured summary of uploaded documents"""
    result, error = generate_summary()

    if error:
        return jsonify({'error': error}), 400

    return jsonify(result)
