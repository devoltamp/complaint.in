from flask import jsonify, Blueprint
from models import Complaint, User
from utils.helpers import serialize_list


analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/stats', methods=['GET'])
def get_stats():
    from app import mongo
    complaint_model = Complaint(mongo.db)
    stats = complaint_model.get_stats()
    return jsonify(stats)

@analytics_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    from app import mongo
    user_model = User(mongo.db)
    users = user_model.get_leaderboard()
    
    leaderboard = []
    for user in users:
        leaderboard.append({
            'name': f"{user['first_name']} {user['last_name']}",
            'initials': user['initials'],
            'verified': user['verified'],
            'complaints': user.get('complaints_count', 0),
            'impact_score': user.get('impact_score', 0),
            'city': user.get('city')
        })
    
    return jsonify(leaderboard)