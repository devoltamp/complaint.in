from bson import ObjectId
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Complaint
from utils.helpers import serialize_list
from flask import Blueprint

profile_bp = Blueprint('profile', __name__)
@profile_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    
    from app import mongo
    user_model = User(mongo.db)
    user = user_model.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's complaints
    complaint_model = Complaint(mongo.db)
    complaints = complaint_model.find_all({'user_id': user['_id']})
    
    # Calculate stats
    resolved = sum(1 for c in complaints if c.get('status') == 'resolved')
    total_upvotes = sum(c.get('upvotes', 0) for c in complaints)
    
    profile = {
        'user': {
            'id': str(user['_id']),
            'name': f"{user['first_name']} {user['last_name']}",
            'initials': user['initials'],
            'email': user['email'],
            'city': user['city'],
            'state': user['state'],
            'verified': user['verified'],
            'joined': user['created_at']
        },
        'stats': {
            'complaints_filed': len(complaints),
            'resolved': resolved,
            'upvotes_received': total_upvotes,
            'impact_score': user.get('impact_score', 0)
        },
        'complaints': serialize_list(complaints)
    }
    
    return jsonify(profile)

@profile_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.json
    
    from app import mongo
    update_data = {}
    
    updatable_fields = ['city', 'state']
    for field in updatable_fields:
        if field in data:
            update_data[field] = data[field]
    
    if update_data:
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
    
    return jsonify({'message': 'Profile updated successfully'})