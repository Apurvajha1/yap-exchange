import os
from flask import Blueprint, request, jsonify, session
from models import db, User
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
ADMIN_USER = os.getenv('ADMIN_USERNAME', 'admin')

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/auth/status', methods=['GET'])
def auth_status():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        today = datetime.now().strftime('%Y-%m-%d')
        if user.last_allowance_date != today and user.username != ADMIN_USER:
            user.balance += 1000.0
            user.last_allowance_date = today
            db.session.commit()
        return jsonify({
            "logged_in": True,
            "username": user.username,
            "balance": user.balance,
            "is_boss": (user.username == ADMIN_USER)
        })
    return jsonify({"logged_in": False})

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    if data['username'].lower() == ADMIN_USER.lower():
        return jsonify({"success": False, "message": "You cannot clone the boss."}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"success": False, "message": "Username taken"}), 400
    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"success": True})

# ... [Keep login and logout exactly the same, but change 'Kinoli' to ADMIN_USER in login] ...
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({"success": True, "balance": user.balance, "is_boss": (user.username == ADMIN_USER)})
    return jsonify({"success": False, "message": "Login failed"}), 401
