from bson import ObjectId
from datetime import datetime

def serialize_doc(doc):
    if doc is None:
        return None
    
    # Create a copy to avoid modifying the original dict during iteration
    doc = dict(doc)
    
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'password' in doc:
        del doc['password'] # Safety: Never send passwords to frontend
    if 'user_id' in doc:
        doc['user_id'] = str(doc['user_id'])
    
    # Handle dates
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
            
    return doc

def serialize_list(docs):
    return [serialize_doc(doc) for doc in docs]