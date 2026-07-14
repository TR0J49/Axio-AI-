"""
Productivity routes - Notes, Tasks, Reminders, Stats endpoints
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.middleware.session import get_session
from app.utils.usage import get_user_email
from app.services.productivity_service import (
    get_all_notes, create_note, delete_note,
    get_all_tasks, create_task, update_task, delete_task,
    get_all_reminders, create_reminder, delete_reminder,
    get_stats
)

productivity_router = APIRouter(tags=["productivity"])


def _email(session: dict) -> str:
    """Extract user email from session for per-user storage."""
    return get_user_email(session) or ''


# ==================== Notes ====================

@productivity_router.get('/notes')
async def list_notes(session: dict = Depends(get_session)):
    """Get all notes"""
    return get_all_notes(email=_email(session))


@productivity_router.post('/notes', status_code=201)
async def create_note_endpoint(request: Request, session: dict = Depends(get_session)):
    """Create a new note"""
    data = await request.json()
    title = data.get('title', 'Untitled')
    content = data.get('content', '')
    note = create_note(title, content, email=_email(session))
    if note:
        return note
    return JSONResponse({'error': 'Failed to create note'}, status_code=500)


@productivity_router.delete('/notes')
async def delete_note_endpoint(request: Request, session: dict = Depends(get_session)):
    """Delete a note"""
    data = await request.json()
    note_id = data.get('id')
    delete_note(note_id, email=_email(session))
    return {'status': 'success'}


# ==================== Tasks ====================

@productivity_router.get('/tasks')
async def list_tasks(session: dict = Depends(get_session)):
    """Get all tasks"""
    return get_all_tasks(email=_email(session))


@productivity_router.post('/tasks', status_code=201)
async def create_task_endpoint(request: Request, session: dict = Depends(get_session)):
    """Create a new task"""
    data = await request.json()
    title = data.get('title', '')
    priority = data.get('priority', 'medium')
    task = create_task(title, priority, email=_email(session))
    if task:
        return task
    return JSONResponse({'error': 'Failed to create task'}, status_code=500)


@productivity_router.put('/tasks')
async def update_task_endpoint(request: Request, session: dict = Depends(get_session)):
    """Update a task"""
    data = await request.json()
    task_id = data.get('id')
    updates = {}
    if 'completed' in data:
        updates['completed'] = data['completed']
    if 'title' in data:
        updates['title'] = data['title']
    if 'priority' in data:
        updates['priority'] = data['priority']

    task = update_task(task_id, updates, email=_email(session))
    if task:
        return task
    return JSONResponse({'error': 'Task not found'}, status_code=404)


@productivity_router.delete('/tasks')
async def delete_task_endpoint(request: Request, session: dict = Depends(get_session)):
    """Delete a task"""
    data = await request.json()
    task_id = data.get('id')
    delete_task(task_id, email=_email(session))
    return {'status': 'success'}


# ==================== Reminders ====================

@productivity_router.get('/reminders')
async def list_reminders(session: dict = Depends(get_session)):
    """Get all reminders"""
    return get_all_reminders(email=_email(session))


@productivity_router.post('/reminders', status_code=201)
async def create_reminder_endpoint(request: Request, session: dict = Depends(get_session)):
    """Create a new reminder"""
    data = await request.json()
    title = data.get('title', '')
    reminder_datetime = data.get('datetime', '')
    reminder = create_reminder(title, reminder_datetime, email=_email(session))
    if reminder:
        return reminder
    return JSONResponse({'error': 'Failed to create reminder'}, status_code=500)


@productivity_router.delete('/reminders')
async def delete_reminder_endpoint(request: Request, session: dict = Depends(get_session)):
    """Delete a reminder"""
    data = await request.json()
    reminder_id = data.get('id')
    delete_reminder(reminder_id, email=_email(session))
    return {'status': 'success'}


# ==================== Stats ====================

@productivity_router.get('/stats')
async def stats(session: dict = Depends(get_session)):
    """Get user statistics"""
    return get_stats(email=_email(session))
