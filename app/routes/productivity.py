"""
Productivity routes - Notes, Tasks, Reminders, Stats endpoints
"""
from flask import Blueprint, request, jsonify

from app.services.productivity_service import (
    get_all_notes, create_note, delete_note,
    get_all_tasks, create_task, update_task, delete_task,
    get_all_reminders, create_reminder, delete_reminder,
    get_stats
)

productivity_bp = Blueprint('productivity', __name__)


# ==================== Notes ====================

@productivity_bp.route('/notes', methods=['GET', 'POST', 'DELETE'])
def notes():
    """Manage notes"""
    if request.method == 'GET':
        return jsonify(get_all_notes())

    elif request.method == 'POST':
        data = request.json
        title = data.get('title', 'Untitled')
        content = data.get('content', '')
        note = create_note(title, content)
        if note:
            return jsonify(note), 201
        return jsonify({'error': 'Failed to create note'}), 500

    elif request.method == 'DELETE':
        note_id = request.json.get('id')
        delete_note(note_id)
        return jsonify({'status': 'success'})


# ==================== Tasks ====================

@productivity_bp.route('/tasks', methods=['GET', 'POST', 'PUT', 'DELETE'])
def tasks():
    """Manage tasks"""
    if request.method == 'GET':
        return jsonify(get_all_tasks())

    elif request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        priority = data.get('priority', 'medium')
        task = create_task(title, priority)
        if task:
            return jsonify(task), 201
        return jsonify({'error': 'Failed to create task'}), 500

    elif request.method == 'PUT':
        task_id = request.json.get('id')
        updates = {}
        if 'completed' in request.json:
            updates['completed'] = request.json['completed']
        if 'title' in request.json:
            updates['title'] = request.json['title']
        if 'priority' in request.json:
            updates['priority'] = request.json['priority']

        task = update_task(task_id, updates)
        if task:
            return jsonify(task)
        return jsonify({'error': 'Task not found'}), 404

    elif request.method == 'DELETE':
        task_id = request.json.get('id')
        delete_task(task_id)
        return jsonify({'status': 'success'})


# ==================== Reminders ====================

@productivity_bp.route('/reminders', methods=['GET', 'POST', 'DELETE'])
def reminders():
    """Manage reminders"""
    if request.method == 'GET':
        return jsonify(get_all_reminders())

    elif request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        reminder_datetime = data.get('datetime', '')
        reminder = create_reminder(title, reminder_datetime)
        if reminder:
            return jsonify(reminder), 201
        return jsonify({'error': 'Failed to create reminder'}), 500

    elif request.method == 'DELETE':
        reminder_id = request.json.get('id')
        delete_reminder(reminder_id)
        return jsonify({'status': 'success'})


# ==================== Stats ====================

@productivity_bp.route('/stats', methods=['GET'])
def stats():
    """Get user statistics"""
    return jsonify(get_stats())
