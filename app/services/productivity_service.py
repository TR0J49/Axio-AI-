"""
Productivity Service - Notes, Tasks, and Reminders management
"""
import uuid
from datetime import datetime

from app.config.settings import USE_MONGODB


# Fallback in-memory storage (used when MongoDB is not available)
user_data = {
    'notes': [],
    'reminders': [],
    'tasks': []
}


def _get_db():
    """Get database instance"""
    from database import get_database
    return get_database()


# ==================== Notes ====================

def get_all_notes():
    """Get all notes"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.get_all_notes()
    return user_data['notes']


def create_note(title, content):
    """Create a new note"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.create_note(title=title, content=content)

    # Fallback to in-memory
    note = {
        'id': str(uuid.uuid4()),
        'title': title,
        'content': content,
        'created': datetime.now().isoformat(),
        'updated': datetime.now().isoformat()
    }
    user_data['notes'].append(note)
    return note


def delete_note(note_id):
    """Delete a note by ID"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db.delete_note(note_id)
        return True

    # Fallback to in-memory
    user_data['notes'] = [n for n in user_data['notes'] if n['id'] != note_id]
    return True


# ==================== Tasks ====================

def get_all_tasks():
    """Get all tasks"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.get_all_tasks()
    return user_data['tasks']


def create_task(title, priority='medium'):
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
        'created': datetime.now().isoformat()
    }
    user_data['tasks'].append(task)
    return task


def update_task(task_id, updates):
    """Update a task"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.update_task(task_id, updates)

    # Fallback to in-memory
    for task in user_data['tasks']:
        if task['id'] == task_id:
            if 'completed' in updates:
                task['completed'] = updates['completed']
            if 'title' in updates:
                task['title'] = updates['title']
            if 'priority' in updates:
                task['priority'] = updates['priority']
            return task
    return None


def delete_task(task_id):
    """Delete a task by ID"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db.delete_task(task_id)
        return True

    # Fallback to in-memory
    user_data['tasks'] = [t for t in user_data['tasks'] if t['id'] != task_id]
    return True


# ==================== Reminders ====================

def get_all_reminders():
    """Get all reminders"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.get_all_reminders()
    return user_data['reminders']


def create_reminder(title, reminder_datetime):
    """Create a new reminder"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        return db.create_reminder(title=title, reminder_datetime=reminder_datetime)

    # Fallback to in-memory
    reminder = {
        'id': str(uuid.uuid4()),
        'title': title,
        'datetime': reminder_datetime,
        'created': datetime.now().isoformat()
    }
    user_data['reminders'].append(reminder)
    return reminder


def delete_reminder(reminder_id):
    """Delete a reminder by ID"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db.delete_reminder(reminder_id)
        return True

    # Fallback to in-memory
    user_data['reminders'] = [r for r in user_data['reminders'] if r['id'] != reminder_id]
    return True


# ==================== Stats ====================

def get_stats():
    """Get user statistics"""
    db = _get_db()
    if USE_MONGODB and db.is_connected():
        db_stats = db.get_stats()
        db_stats['current_time'] = datetime.now().isoformat()
        return db_stats

    # Fallback to in-memory
    total_tasks = len(user_data['tasks'])
    completed_tasks = len([t for t in user_data['tasks'] if t['completed']])

    return {
        'total_notes': len(user_data['notes']),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': total_tasks - completed_tasks,
        'total_reminders': len(user_data['reminders']),
        'current_time': datetime.now().isoformat()
    }
