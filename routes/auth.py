from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User
from utils.helpers import serialize_doc

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        print("Register data:", data)
        required = ['email', 'password', 'first_name', 'last_name', 'city', 'state']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        from app import mongo
        from flask import current_app
        print("MONGO_URI:", current_app.config.get('MONGO_URI'))
        print("mongo.cx:", mongo.cx)
        print("mongo.db:", mongo.db)
        user_model = User(mongo.db)
        
        if user_model.find_by_email(data['email']):
            return jsonify({'error': 'Email already registered'}), 400
        
        user = user_model.create_user(
            data['email'], data['password'], data['first_name'],
            data['last_name'], data['city'], data['state']
        )
        
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({
            'token': access_token,
            'user': serialize_doc(user)
        }), 201
    except Exception as e:
        print(f"Error in register: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    from app import mongo
    user_model = User(mongo.db)
    user = user_model.find_by_email(email)
    
    if not user or not user_model.verify_password(user, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({
        'token': access_token,
        'user': serialize_doc(user)
    })

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    from app import mongo
    user_model = User(mongo.db)
    user = user_model.find_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(serialize_doc(user))