from flask import Blueprint, request, jsonify
from controllers.user_controller import UserController

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    result, status = UserController.list_users()
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    result, status = UserController.get_user(user_id)
    return jsonify(result), status


@user_bp.route('/users', methods=['POST'])
def create_user():
    result, status = UserController.create_user(request.get_json())
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    result, status = UserController.update_user(user_id, request.get_json())
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    result, status = UserController.delete_user(user_id)
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    result, status = UserController.get_user_tasks(user_id)
    return jsonify(result), status


@user_bp.route('/login', methods=['POST'])
def login():
    result, status = UserController.login(request.get_json())
    return jsonify(result), status
