from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
complaints_bp = Blueprint('complaints', __name__, url_prefix='/api/complaints')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')