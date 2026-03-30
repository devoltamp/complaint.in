from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Complaint, User
from utils.helpers import serialize_doc, serialize_list
from bson import ObjectId
from flask import Blueprint
# from extensions import mongo   # or keep app import if not changed yet

complaints_bp = Blueprint('complaints', __name__)
@complaints_bp.route('/', methods=['GET'])
def get_complaints():
    category = request.args.get('category')
    sort_by = request.args.get('sort', 'latest')
    limit = int(request.args.get('limit', 50))
    skip = int(request.args.get('skip', 0))
    search = request.args.get('search')
    
    from app import mongo
    complaint_model = Complaint(mongo.db)
    
    # Build filters
    filters = {}
    if category and category != 'all':
        filters['category'] = category
    
    # Search
    if search:
        complaints = complaint_model.search(search)
    else:
        complaints = complaint_model.find_all(filters, sort_by, limit, skip)
    
    # Add user details to each complaint
    user_model = User(mongo.db)
    for complaint in complaints:
        user = user_model.find_by_id(complaint['user_id'])
        if user:
            complaint['user'] = {
                'name': f"{user['first_name']} {user['last_name']}",
                'initials': user['initials'],
                'verified': user['verified']
            }
    
    return jsonify(serialize_list(complaints))

@complaints_bp.route('/', methods=['POST'])
@jwt_required()
def create_complaint():
    user_id = get_jwt_identity()
    data = request.json
    
    required = ['title', 'category', 'description', 'city', 'state', 'urgency']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    from app import mongo
    complaint_model = Complaint(mongo.db)
    
    complaint_id = complaint_model.create_complaint(
        user_id=user_id,
        title=data['title'],
        category=data['category'],
        description=data['description'],
        city=data['city'],
        state=data['state'],
        urgency=data['urgency'],
        tags=data.get('tags', []),
        location=data.get('location')
    )
    
    # Update user's complaint count
    user_model = User(mongo.db)
    user_model.increment_complaints(user_id)
    
    return jsonify({'id': str(complaint_id), 'message': 'Complaint created successfully'}), 201

@complaints_bp.route('/<complaint_id>', methods=['GET'])
def get_complaint(complaint_id):
    from app import mongo
    complaint_model = Complaint(mongo.db)
    complaint = complaint_model.find_by_id(complaint_id)
    
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
    
    # Add user details
    user_model = User(mongo.db)
    user = user_model.find_by_id(complaint['user_id'])
    if user:
        complaint['user'] = {
            'name': f"{user['first_name']} {user['last_name']}",
            'initials': user['initials'],
            'verified': user['verified']
        }
    
    # Add commenter details
    for comment in complaint.get('comments', []):
        comment_user = user_model.find_by_id(comment['user_id'])
        if comment_user:
            comment['user'] = {
                'name': f"{comment_user['first_name']} {comment_user['last_name']}",
                'initials': comment_user['initials']
            }
    
    return jsonify(serialize_doc(complaint))

@complaints_bp.route('/<complaint_id>/vote', methods=['POST'])
@jwt_required()
def vote_complaint(complaint_id):
    user_id = get_jwt_identity()
    data = request.json
    vote_type = data.get('vote_type')
    
    if vote_type not in ['up', 'down']:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    from app import mongo
    complaint_model = Complaint(mongo.db)
    result = complaint_model.vote(complaint_id, user_id, vote_type)
    
    if not result:
        return jsonify({'error': 'Complaint not found'}), 404
    
    return jsonify({'message': 'Vote recorded successfully'})

@complaints_bp.route('/<complaint_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(complaint_id):
    user_id = get_jwt_identity()
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Comment text required'}), 400
    
    from app import mongo
    complaint_model = Complaint(mongo.db)
    result = complaint_model.add_comment(complaint_id, user_id, text)
    
    if not result:
        return jsonify({'error': 'Complaint not found'}), 404
    
    return jsonify({'message': 'Comment added successfully'})

@complaints_bp.route('/<complaint_id>/status', methods=['PUT'])
@jwt_required()
def update_status(complaint_id):
    user_id = get_jwt_identity()
    data = request.json
    status = data.get('status')
    
    valid_statuses = ['open', 'review', 'resolved']
    if status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    from app import mongo
    complaint_model = Complaint(mongo.db)
    complaint = complaint_model.find_by_id(complaint_id)
    
    # Only the complaint owner or admin can update status
    if str(complaint['user_id']) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    complaint_model.update_status(complaint_id, status)
    
    return jsonify({'message': 'Status updated successfully'})

@complaints_bp.route('/<complaint_id>/follow', methods=['POST'])
@jwt_required()
def follow_complaint(complaint_id):
    user_id = get_jwt_identity()
    
    from app import mongo
    user_model = User(mongo.db)
    user_model.add_following(user_id, complaint_id)
    
    return jsonify({'message': 'Following complaint'})

@complaints_bp.route('/<complaint_id>/auth-response', methods=['POST'])
@jwt_required()
def add_auth_response(complaint_id):
    user_id = get_jwt_identity()
    data = request.json
    response = data.get('response')
    
    if not response:
        return jsonify({'error': 'Response text required'}), 400
    
    from app import mongo
    complaint_model = Complaint(mongo.db)
    complaint = complaint_model.find_by_id(complaint_id)
    
    # In production, check if user is actually an authority
    # For now, allow any verified user
    
    complaint_model.add_auth_response(complaint_id, response)
    
    return jsonify({'message': 'Authority response added'})