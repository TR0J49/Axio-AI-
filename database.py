"""
MongoDB Database Module for Axio AI
Handles all database operations for chat, tasks, notes, reminders, DocIQ, and VizIQ
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from bson import ObjectId
import os

class Database:
    """MongoDB Database Handler for Axio AI"""

    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False

    def connect(self, uri=None, database_name=None):
        """Connect to MongoDB"""
        try:
            uri = uri or os.getenv('MONGODB_URI')
            database_name = database_name or os.getenv('MONGODB_DATABASE', 'axio_ai')

            if not uri:
                print("[WARNING] MongoDB URI not found. Using in-memory storage.")
                return False

            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            self.connected = True
            print(f"[OK] Connected to MongoDB database: {database_name}")

            # Create indexes for better performance
            self._create_indexes()

            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"[ERROR] MongoDB error: {e}")
            self.connected = False
            return False

    def _create_indexes(self):
        """Create indexes for collections"""
        try:
            # Chat messages index
            self.db.chat_messages.create_index([("session_id", 1), ("created_at", -1)])

            # Tasks index
            self.db.tasks.create_index([("created_at", -1)])
            self.db.tasks.create_index([("completed", 1)])

            # Notes index
            self.db.notes.create_index([("created_at", -1)])

            # Reminders index
            self.db.reminders.create_index([("datetime", 1)])
            self.db.reminders.create_index([("created_at", -1)])

            # DocIQ index
            self.db.dociq_documents.create_index([("session_id", 1)])
            self.db.dociq_conversations.create_index([("session_id", 1), ("created_at", -1)])

            # VizIQ index
            self.db.viziq_data.create_index([("created_at", -1)])

            print("[OK] Database indexes created")
        except Exception as e:
            print(f"[WARNING] Index creation warning: {e}")

    def is_connected(self):
        """Check if database is connected"""
        return self.connected and self.client is not None

    # ========================
    # Chat Messages Operations
    # ========================

    def save_chat_message(self, session_id, role, content, metadata=None):
        """Save a chat message"""
        if not self.is_connected():
            return None

        message = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }

        result = self.db.chat_messages.insert_one(message)
        return str(result.inserted_id)

    def get_chat_history(self, session_id, limit=50):
        """Get chat history for a session"""
        if not self.is_connected():
            return []

        messages = self.db.chat_messages.find(
            {"session_id": session_id}
        ).sort("created_at", 1).limit(limit)

        return [self._serialize_doc(msg) for msg in messages]

    def update_chat_message(self, message_id, new_content):
        """Update a chat message"""
        if not self.is_connected():
            return False

        result = self.db.chat_messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"content": new_content, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def delete_chat_messages_after(self, session_id, message_id):
        """Delete all messages after a specific message"""
        if not self.is_connected():
            return False

        # Get the message to find its timestamp
        message = self.db.chat_messages.find_one({"_id": ObjectId(message_id)})
        if not message:
            return False

        # Delete all messages after this one
        result = self.db.chat_messages.delete_many({
            "session_id": session_id,
            "created_at": {"$gt": message["created_at"]}
        })
        return result.deleted_count >= 0

    def clear_chat_history(self, session_id):
        """Clear all chat history for a session"""
        if not self.is_connected():
            return False

        result = self.db.chat_messages.delete_many({"session_id": session_id})
        return result.deleted_count >= 0

    # ========================
    # Tasks Operations
    # ========================

    def create_task(self, title, priority="medium", completed=False):
        """Create a new task"""
        if not self.is_connected():
            return None

        task = {
            "title": title,
            "priority": priority,
            "completed": completed,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = self.db.tasks.insert_one(task)
        task["id"] = str(result.inserted_id)
        return self._serialize_doc(task)

    def get_all_tasks(self):
        """Get all tasks"""
        if not self.is_connected():
            return []

        tasks = self.db.tasks.find().sort("created_at", -1)
        return [self._serialize_doc(task) for task in tasks]

    def update_task(self, task_id, updates):
        """Update a task"""
        if not self.is_connected():
            return None

        updates["updated_at"] = datetime.utcnow()

        result = self.db.tasks.find_one_and_update(
            {"_id": ObjectId(task_id)},
            {"$set": updates},
            return_document=True
        )

        return self._serialize_doc(result) if result else None

    def delete_task(self, task_id):
        """Delete a task"""
        if not self.is_connected():
            return False

        result = self.db.tasks.delete_one({"_id": ObjectId(task_id)})
        return result.deleted_count > 0

    # ========================
    # Notes Operations
    # ========================

    def create_note(self, title, content=""):
        """Create a new note"""
        if not self.is_connected():
            return None

        note = {
            "title": title,
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = self.db.notes.insert_one(note)
        note["id"] = str(result.inserted_id)
        return self._serialize_doc(note)

    def get_all_notes(self):
        """Get all notes"""
        if not self.is_connected():
            return []

        notes = self.db.notes.find().sort("created_at", -1)
        return [self._serialize_doc(note) for note in notes]

    def update_note(self, note_id, updates):
        """Update a note"""
        if not self.is_connected():
            return None

        updates["updated_at"] = datetime.utcnow()

        result = self.db.notes.find_one_and_update(
            {"_id": ObjectId(note_id)},
            {"$set": updates},
            return_document=True
        )

        return self._serialize_doc(result) if result else None

    def delete_note(self, note_id):
        """Delete a note"""
        if not self.is_connected():
            return False

        result = self.db.notes.delete_one({"_id": ObjectId(note_id)})
        return result.deleted_count > 0

    # ========================
    # Reminders Operations
    # ========================

    def create_reminder(self, title, reminder_datetime):
        """Create a new reminder"""
        if not self.is_connected():
            return None

        reminder = {
            "title": title,
            "datetime": reminder_datetime,
            "created_at": datetime.utcnow()
        }

        result = self.db.reminders.insert_one(reminder)
        reminder["id"] = str(result.inserted_id)
        return self._serialize_doc(reminder)

    def get_all_reminders(self):
        """Get all reminders"""
        if not self.is_connected():
            return []

        reminders = self.db.reminders.find().sort("datetime", 1)
        return [self._serialize_doc(reminder) for reminder in reminders]

    def delete_reminder(self, reminder_id):
        """Delete a reminder"""
        if not self.is_connected():
            return False

        result = self.db.reminders.delete_one({"_id": ObjectId(reminder_id)})
        return result.deleted_count > 0

    # ========================
    # DocIQ Operations
    # ========================

    def save_dociq_document(self, session_id, doc_info):
        """Save a DocIQ document"""
        if not self.is_connected():
            return None

        document = {
            "session_id": session_id,
            "doc_id": doc_info.get("id"),
            "name": doc_info.get("name"),
            "original_name": doc_info.get("original_name"),
            "extension": doc_info.get("extension"),
            "size": doc_info.get("size"),
            "path": doc_info.get("path"),
            "text_length": doc_info.get("text_length"),
            "chunks": doc_info.get("chunks", []),
            "chunk_count": doc_info.get("chunk_count", 0),
            "status": doc_info.get("status", "ready"),
            "uploaded_at": datetime.utcnow()
        }

        result = self.db.dociq_documents.insert_one(document)
        return str(result.inserted_id)

    def get_dociq_documents(self, session_id=None):
        """Get DocIQ documents (all or by session)"""
        if not self.is_connected():
            return []

        query = {"session_id": session_id} if session_id else {}
        documents = self.db.dociq_documents.find(query).sort("uploaded_at", -1)
        return [self._serialize_doc(doc) for doc in documents]

    def delete_dociq_document(self, doc_id):
        """Delete a DocIQ document"""
        if not self.is_connected():
            return False

        result = self.db.dociq_documents.delete_one({"doc_id": doc_id})
        return result.deleted_count > 0

    def clear_dociq_documents(self, session_id=None):
        """Clear DocIQ documents"""
        if not self.is_connected():
            return False

        query = {"session_id": session_id} if session_id else {}
        result = self.db.dociq_documents.delete_many(query)
        return result.deleted_count >= 0

    def save_dociq_conversation(self, session_id, role, content):
        """Save a DocIQ conversation message"""
        if not self.is_connected():
            return None

        message = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow()
        }

        result = self.db.dociq_conversations.insert_one(message)
        return str(result.inserted_id)

    def get_dociq_conversation(self, session_id, limit=20):
        """Get DocIQ conversation history"""
        if not self.is_connected():
            return []

        messages = self.db.dociq_conversations.find(
            {"session_id": session_id}
        ).sort("created_at", 1).limit(limit)

        return [self._serialize_doc(msg) for msg in messages]

    def clear_dociq_conversation(self, session_id):
        """Clear DocIQ conversation"""
        if not self.is_connected():
            return False

        result = self.db.dociq_conversations.delete_many({"session_id": session_id})
        return result.deleted_count >= 0

    # ========================
    # VizIQ Operations
    # ========================

    def save_viziq_data(self, session_id, data_info):
        """Save VizIQ data analysis"""
        if not self.is_connected():
            return None

        viziq_record = {
            "session_id": session_id,
            "filename": data_info.get("filename"),
            "columns": data_info.get("columns", []),
            "dtypes": data_info.get("dtypes", {}),
            "stats": data_info.get("stats", {}),
            "row_count": data_info.get("row_count", 0),
            "kpis": data_info.get("kpis", []),
            "charts": data_info.get("charts", []),
            "insights": data_info.get("insights", []),
            "preview_data": data_info.get("preview_data", [])[:100],  # Store first 100 rows
            "dashboard_name": data_info.get("dashboard_name"),
            "created_at": datetime.utcnow()
        }

        # Upsert - update if exists, insert if not
        result = self.db.viziq_data.update_one(
            {"session_id": session_id},
            {"$set": viziq_record},
            upsert=True
        )

        return str(result.upserted_id) if result.upserted_id else "updated"

    def get_viziq_data(self, session_id):
        """Get VizIQ data for a session"""
        if not self.is_connected():
            return None

        data = self.db.viziq_data.find_one({"session_id": session_id})
        return self._serialize_doc(data) if data else None

    def clear_viziq_data(self, session_id):
        """Clear VizIQ data for a session"""
        if not self.is_connected():
            return False

        result = self.db.viziq_data.delete_one({"session_id": session_id})
        return result.deleted_count > 0

    # ========================
    # Statistics Operations
    # ========================

    def get_stats(self):
        """Get overall statistics"""
        if not self.is_connected():
            return {
                "total_notes": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "total_reminders": 0,
                "total_documents": 0,
                "total_chat_messages": 0
            }

        total_tasks = self.db.tasks.count_documents({})
        completed_tasks = self.db.tasks.count_documents({"completed": True})

        return {
            "total_notes": self.db.notes.count_documents({}),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks,
            "total_reminders": self.db.reminders.count_documents({}),
            "total_documents": self.db.dociq_documents.count_documents({}),
            "total_chat_messages": self.db.chat_messages.count_documents({})
        }

    # ========================
    # Utility Methods
    # ========================

    def _serialize_doc(self, doc):
        """Convert MongoDB document to JSON-serializable dict"""
        if doc is None:
            return None

        doc = dict(doc)

        # Convert ObjectId to string
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]

        # Convert datetime objects to ISO format strings
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif isinstance(value, ObjectId):
                doc[key] = str(value)

        return doc

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.connected = False
            print("[OK] MongoDB connection closed")


# Global database instance
db = Database()


def init_database():
    """Initialize database connection"""
    return db.connect()


def get_database():
    """Get database instance"""
    return db
