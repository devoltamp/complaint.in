import os
from flask import Flask, send_from_directory
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config

load_dotenv()

# Global extensions
mongo = PyMongo()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config.from_object(Config)
    
    # Ensure MONGO_URI has a database name
    if 'MONGO_URI' in app.config and app.config['MONGO_URI']:
        uri_parts = app.config['MONGO_URI'].rstrip('/').split('/')
        if len(uri_parts) < 4 or not uri_parts[-1]:
            app.config['MONGO_URI'] = app.config['MONGO_URI'].rstrip('/') + '/complaint_app'
    
    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # Register blueprints (Import inside to prevent circular issues)
    from routes import auth_bp, complaints_bp, analytics_bp, profile_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(complaints_bp, url_prefix='/complaints')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    # Serve static files
    @app.route('/')
    def serve_index():
        return send_from_directory('static', 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('static', path)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)