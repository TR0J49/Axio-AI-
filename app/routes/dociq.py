"""
DocIQ routes - Document Intelligence endpoints
"""
from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

from app.config.settings import UPLOAD_FOLDER, MAX_UPLOAD_SIZE
from app.utils.file_helpers import allowed_file
from app.services.dociq_service import (
    get_dociq_documents, get_dociq_session_id,
    process_document_upload, delete_document, clear_all_documents,
    generate_dociq_response, save_chat_message, generate_summary
)
from app.middleware.session import get_session

dociq_router = APIRouter(tags=["dociq"])


@dociq_router.post('/upload')
async def dociq_upload(file: UploadFile = File(...), session: dict = Depends(get_session)):
    """Upload and process document for DocIQ"""
    if not file.filename:
        return JSONResponse({'error': 'No file selected'}, status_code=400)

    if not allowed_file(file.filename):
        return JSONResponse(
            {'error': 'File type not supported. Use PDF, DOC, DOCX, or TXT.'},
            status_code=400
        )

    try:
        file_bytes = await file.read()
        if len(file_bytes) > MAX_UPLOAD_SIZE:
            return JSONResponse(
                {'error': f'File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)} MB.'},
                status_code=413
            )
        doc_info, error = process_document_upload(file_bytes, file.filename, UPLOAD_FOLDER, session)

        if error:
            return JSONResponse({'error': error}, status_code=500)

        return {
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
        }

    except Exception as e:
        print(f"DocIQ upload error: {e}")
        return JSONResponse({'error': f'Failed to process document: {str(e)}'}, status_code=500)


@dociq_router.get('/documents')
async def dociq_list_documents(session: dict = Depends(get_session)):
    """List all uploaded documents"""
    session_data = get_dociq_documents(session)

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

    return {'documents': documents}


@dociq_router.delete('/documents/{doc_id}')
async def dociq_delete_document(doc_id: str, session: dict = Depends(get_session)):
    """Delete a specific document"""
    if delete_document(session, doc_id):
        return {'success': True, 'message': 'Document deleted'}
    return JSONResponse({'error': 'Document not found'}, status_code=404)


@dociq_router.post('/clear')
async def dociq_clear(session: dict = Depends(get_session)):
    """Clear all documents and conversation"""
    clear_all_documents(session)
    return {'success': True, 'message': 'All documents cleared'}


@dociq_router.post('/chat')
async def dociq_chat(request: Request, session: dict = Depends(get_session)):
    """Chat with documents using RAG"""
    from app.utils.usage import check_and_increment
    exceeded, used, limit = check_and_increment(session)
    if exceeded:
        return JSONResponse(
            {'error': 'free_tier_limit_reached', 'payment_required': True, 'used': used, 'limit': limit},
            status_code=402
        )

    data = await request.json()
    user_message = data.get('message', '')

    print(f"[DocIQ Chat] Received message: {user_message[:50]}...")

    if not user_message:
        return JSONResponse({'error': 'No message provided'}, status_code=400)

    session_data = get_dociq_documents(session)

    print(f"[DocIQ Chat] Documents found: {len(session_data['documents'])}")
    for doc in session_data['documents']:
        doc_name = doc.get('name', 'Unknown')
        chunk_count = doc.get('chunk_count', 0)
        print(f"[DocIQ Chat] - {doc_name}: {chunk_count} chunks")

    if not session_data['documents']:
        print("[DocIQ Chat] No documents found - returning error")
        return {
            'response': "Please upload some documents first. I need document content to provide accurate answers.",
            'has_documents': False
        }

    # Save user message
    save_chat_message(session, 'user', user_message)

    # Generate response using RAG
    ai_response = generate_dociq_response(user_message, session_data)

    # Save AI response
    save_chat_message(session, 'assistant', ai_response)

    return {
        'response': ai_response,
        'has_documents': True,
        'document_count': len(session_data['documents']),
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    }


@dociq_router.get('/summary')
async def dociq_summary(session: dict = Depends(get_session)):
    """Get structured summary of uploaded documents"""
    result, error = generate_summary(session)

    if error:
        return JSONResponse({'error': error}, status_code=400)

    return result
