"""
Routes for call record management
"""
from flask import Blueprint
from controllers.calls_controller import calls_controller

calls_routes = Blueprint('calls', __name__)

# API Routes
@calls_routes.route('/api/calls', methods=['POST'])
def upload_call():
    """Upload and process an audio file"""
    return calls_controller.upload_and_process()

@calls_routes.route('/api/calls', methods=['GET'])
def get_all_calls():
    """Get all call records with optional filtering by tag"""
    return calls_controller.get_all()

@calls_routes.route('/api/calls/analytics', methods=['GET'])
def get_analytics():
    """Get analytics about calls"""
    return calls_controller.get_analytics()

@calls_routes.route('/api/calls/<call_id>', methods=['GET'])
def get_call(call_id):
    """Get a single call record by ID"""
    return calls_controller.get_one(call_id)

@calls_routes.route('/api/calls/<call_id>/tags', methods=['PUT'])
def update_call_tags(call_id):
    """Update/override tags for a call record"""
    return calls_controller.update_tags(call_id)

@calls_routes.route('/api/calls/<call_id>/export', methods=['GET'])
def export_call(call_id):
    """Export a call record as JSON"""
    return calls_controller.export_call(call_id)

@calls_routes.route('/api/calls/<call_id>', methods=['DELETE'])
def delete_call(call_id):
    """Delete a call record"""
    return calls_controller.delete_one(call_id)

