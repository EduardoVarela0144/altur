"""
Routes for authentication
"""
from flask import Blueprint
from controllers.auth_controller import auth_controller

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    return auth_controller.register()

@auth_routes.route('/api/auth/login', methods=['POST'])
def login():
    """Login a user"""
    return auth_controller.login()

@auth_routes.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout a user"""
    return auth_controller.logout()

