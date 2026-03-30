from bson import ObjectId
from datetime import datetime
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    doc['_id'] = str(doc['_id'])
    if 'user_id' in doc and isinstance(doc['user_id'], ObjectId):
        doc['user_id'] = str(doc['user_id'])
    if 'comments' in doc:
        for comment in doc['comments']:
            if 'user_id' in comment and isinstance(comment['user_id'], ObjectId):
                comment['user_id'] = str(comment['user_id'])
            if 'created_at' in comment:
                comment['created_at'] = comment['created_at'].isoformat()
    return doc

def serialize_list(docs):
    return [serialize_doc(doc) for doc in docs]