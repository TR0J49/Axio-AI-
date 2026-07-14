"""
Productivity Service - Notes, Tasks, and Reminders management
"""
import uuid
from datetime import datetime, timezone

from app.config.settings import USE_MONGODB


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'


# Fallback in-memory storage keyed by user email to isolate users
_user_data: dict[str, dict] = {}


def _get_fallback_store(email: str) -> dict:
    if email not in _user_data:
        _user_data[email] = {'notes': [], 'reminders': [], 'tasks': []}
    return _user_data[email]


def _get_db():
    """Get database instance"""
    from database import get_database
    return get_database()


# ==================== Notes ====================

def get_all_notes(email: str = ''):
    """Get all notes"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.get_all_notes()
    return _get_fallback_store(email)['notes']


def create_note(title, content, email: str = ''):
    """Create a new note"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.create_note(title=title, content=content)

    # Fallback to in-memory
    now = _utcnow_iso()
    note = {
        'id': str(uuid.uuid4()),
        'title': title,
        'content': content,
        'created': now,
        'updated': now
    }
    _get_fallback_store(email)['notes'].append(note)
    return note


def delete_note(note_id, email: str = ''):
    """Delete a note by ID"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db.delete_note(note_id)
        return True

    store = _get_fallback_store(email)
    store['notes'] = [n for n in store['notes'] if n['id'] != note_id]
    return True


# ==================== Tasks ====================

def get_all_tasks(email: str = ''):
    """Get all tasks"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.get_all_tasks()
    return _get_fallback_store(email)['tasks']


def create_task(title, priority='medium', email: str = ''):
    """Create a new task"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.create_task(title=title, priority=priority)

    # Fallback to in-memory
    task = {
        'id': str(uuid.uuid4()),
        'title': title,
        'completed': False,
        'priority': priority,
        'created': _utcnow_iso()
    }
    _get_fallback_store(email)['tasks'].append(task)
    return task


def update_task(task_id, updates, email: str = ''):
    """Update a task"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.update_task(task_id, updates)

    for task in _get_fallback_store(email)['tasks']:
        if task['id'] == task_id:
            if 'completed' in updates:
                task['completed'] = updates['completed']
            if 'title' in updates:
                task['title'] = updates['title']
            if 'priority' in updates:
                task['priority'] = updates['priority']
            return task
    return None


def delete_task(task_id, email: str = ''):
    """Delete a task by ID"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db.delete_task(task_id)
        return True

    store = _get_fallback_store(email)
    store['tasks'] = [t for t in store['tasks'] if t['id'] != task_id]
    return True


# ==================== Reminders ====================

def get_all_reminders(email: str = ''):
    """Get all reminders"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.get_all_reminders()
    return _get_fallback_store(email)['reminders']


def create_reminder(title, reminder_datetime, email: str = ''):
    """Create a new reminder"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.create_reminder(title=title, reminder_datetime=reminder_datetime)

    reminder = {
        'id': str(uuid.uuid4()),
        'title': title,
        'datetime': reminder_datetime,
        'created': _utcnow_iso()
    }
    _get_fallback_store(email)['reminders'].append(reminder)
    return reminder


def delete_reminder(reminder_id, email: str = ''):
    """Delete a reminder by ID"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db.delete_reminder(reminder_id)
        return True

    store = _get_fallback_store(email)
    store['reminders'] = [r for r in store['reminders'] if r['id'] != reminder_id]
    return True


# ==================== Stats ====================

def get_stats(email: str = ''):
    """Get user statistics"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db_stats = db.get_stats()
        db_stats['current_time'] = _utcnow_iso()
        return db_stats

    store = _get_fallback_store(email)
    total_tasks = len(store['tasks'])
    completed_tasks = len([t for t in store['tasks'] if t['completed']])

    return {
        'total_notes': len(store['notes']),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': total_tasks - completed_tasks,
        'total_reminders': len(store['reminders']),
        'current_time': _utcnow_iso()
    }
