from flask import jsonify, Blueprint
from models import Complaint, User
from utils.helpers import serialize_list


analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/stats', methods=['GET'])
def get_stats():
    from app import mongo
    complaint_model = Complaint(mongo.db)
    try:
        stats = complaint_model.get_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"Error in get_stats: {e}")
        return jsonify({'total': 0, 'resolved': 0, 'open': 0, 'resolution_rate': 0, 'categories': [], 'top_cities': []})

@analytics_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    from app import mongo
    user_model = User(mongo.db)
    try:
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
    except Exception as e:
        print(f"Error in get_leaderboard: {e}")
        return jsonify([])