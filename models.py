from datetime import datetime
from bson import ObjectId
import bcrypt

class User:
    def __init__(self, db):
        self.collection = db.users
    
    def create_user(self, email, password, first_name, last_name, city, state):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = {
            'email': email,
            'password': hashed,
            'first_name': first_name,
            'last_name': last_name,
            'initials': (first_name[0] + (last_name[0] if last_name else '')).upper(),
            'city': city,
            'state': state,
            'verified': False,
            'created_at': datetime.utcnow(),
            'complaints_count': 0,
            'upvotes_received': 0,
            'impact_score': 0,
            'following': []
        }
        
        result = self.collection.insert_one(user)
        user['_id'] = result.inserted_id
        return user
    
    def find_by_email(self, email):
        return self.collection.find_one({'email': email})
    
    def find_by_id(self, user_id):
        return self.collection.find_one({'_id': ObjectId(user_id)})
    
    def verify_password(self, user, password):
        return bcrypt.checkpw(password.encode('utf-8'), user['password'])
    
    def increment_complaints(self, user_id):
        self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'complaints_count': 1}}
        )
    
    def update_impact_score(self, user_id, points):
        self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'impact_score': points}}
        )
    
    def add_following(self, user_id, complaint_id):
        self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$addToSet': {'following': complaint_id}}
        )
    
    def get_leaderboard(self, limit=5):
        return list(self.collection.find(
            {},
            {'password': 0}
        ).sort([('impact_score', -1)]).limit(limit))

class Complaint:
    def __init__(self, db):
        self.collection = db.complaints
        self.user_collection = db.users
    
    def create_complaint(self, user_id, title, category, description, city, state, 
                         urgency, tags=None, location=None):
        complaint = {
            'user_id': ObjectId(user_id),
            'title': title,
            'category': category,
            'description': description,
            'city': city,
            'state': state,
            'urgency': urgency,
            'tags': tags or [],
            'location': location,
            'upvotes': 0,
            'downvotes': 0,
            'comments': [],
            'votes': {},  # Track who voted and how
            'proofs': [],
            'status': 'open',  # open, review, resolved
            'viral': False,
            'pinned': False,
            'auth_response': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = self.collection.insert_one(complaint)
        return result.inserted_id
    
    def find_all(self, filters=None, sort_by='latest', limit=50, skip=0):
        query = filters or {}
        
        # Build sort order
        sort_order = [('created_at', -1)]  # latest default
        if sort_by == 'trending':
            # Trending = (upvotes - downvotes) / age in days
            sort_order = [('upvotes', -1), ('downvotes', 1)]
        elif sort_by == 'critical':
            sort_order = [('upvotes', -1)]
        
        return list(self.collection.find(query).sort(sort_order).skip(skip).limit(limit))
    
    def find_by_id(self, complaint_id):
        return self.collection.find_one({'_id': ObjectId(complaint_id)})
    
    def vote(self, complaint_id, user_id, vote_type):
        complaint = self.find_by_id(complaint_id)
        if not complaint:
            return False
        
        user_id_str = str(user_id)
        old_vote = complaint.get('votes', {}).get(user_id_str)
        
        # Remove old vote if exists
        if old_vote:
            if old_vote == 'up':
                self.collection.update_one(
                    {'_id': ObjectId(complaint_id)},
                    {'$inc': {'upvotes': -1}}
                )
            elif old_vote == 'down':
                self.collection.update_one(
                    {'_id': ObjectId(complaint_id)},
                    {'$inc': {'downvotes': -1}}
                )
        
        # Add new vote
        if vote_type == 'up':
            self.collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'upvotes': 1},
                    '$set': {f'votes.{user_id_str}': 'up'}
                }
            )
        elif vote_type == 'down':
            self.collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'downvotes': 1},
                    '$set': {f'votes.{user_id_str}': 'down'}
                }
            )
        
        # Update user's impact score based on vote changes
        impact_change = 1 if vote_type == 'up' else -0.5
        user_model = User(self.collection.database)
        user_model.update_impact_score(complaint['user_id'], impact_change)
        
        return True
    
    def add_comment(self, complaint_id, user_id, text):
        comment = {
            'user_id': ObjectId(user_id),
            'text': text,
            'created_at': datetime.utcnow()
        }
        
        self.collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$push': {'comments': comment}}
        )
        
        return True
    
    def update_status(self, complaint_id, status):
        self.collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {
                '$set': {
                    'status': status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    def add_proof(self, complaint_id, proof_url):
        self.collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$push': {'proofs': proof_url}}
        )
    
    def add_auth_response(self, complaint_id, response):
        self.collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': {
                'auth_response': response,
                'status': 'review',
                'updated_at': datetime.utcnow()
            }}
        )
    
    def get_stats(self):
        total = self.collection.count_documents({})
        resolved = self.collection.count_documents({'status': 'resolved'})
        open_count = self.collection.count_documents({'status': 'open'})
        
        # Get category distribution
        categories = self.collection.aggregate([
            {'$group': {
                '_id': '$category',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ])
        
        # Get city distribution
        cities = self.collection.aggregate([
            {'$group': {
                '_id': '$city',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ])
        
        return {
            'total': total,
            'resolved': resolved,
            'open': open_count,
            'resolution_rate': (resolved / total * 100) if total > 0 else 0,
            'categories': list(categories),
            'top_cities': list(cities)
        }
    
    def search(self, query):
        return list(self.collection.find({
            '$or': [
                {'title': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}},
                {'city': {'$regex': query, '$options': 'i'}}
            ]
        }).sort([('upvotes', -1)]).limit(30))