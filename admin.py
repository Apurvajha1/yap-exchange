import os
from flask import Blueprint, request, jsonify, session, render_template
from models import db, User, Target
from payouts import execute_payout
from dotenv import load_dotenv

load_dotenv()
ADMIN_USER = os.getenv('ADMIN_USERNAME', 'admin')

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/boss')
def boss_panel():
    if 'user_id' not in session: return "Access Denied: Not Logged In", 401
    user = User.query.get(session['user_id'])
    if user.username != ADMIN_USER: return "Access Denied: You are not the Boss.", 403
    return render_template('admin.html')

@admin_bp.route('/api/admin/resolve', methods=['POST'])
def resolve_bounty():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    user = User.query.get(session['user_id'])
    if user.username != ADMIN_USER: return jsonify({"error": "Nice try, NPC."}), 403

    data = request.json
    execute_payout(data['target_name'], data['duration'])
    return jsonify({"success": True})
