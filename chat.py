import os
from flask import Blueprint, request, jsonify, session
from models import User
import time
from dotenv import load_dotenv

load_dotenv()
ADMIN_USER = os.getenv('ADMIN_USERNAME', 'admin')

chat_bp = Blueprint('chat_bp', __name__)
# ... [Keep cleanup_chat and get_chat the same] ...

@chat_bp.route('/api/chat', methods=['POST'])
def post_chat():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    user = User.query.get(session['user_id'])
    data = request.json
    text = data.get('text', '').strip()

    if not text: return jsonify({"error": "Empty yapping"}), 400
    cleanup_chat()

    new_msg = {
        "id": time.time(),
        "username": user.username,
        "is_admin": (user.username == ADMIN_USER),
        "text": text,
        "timestamp": time.time()
    }
    chat_messages.append(new_msg)
    if len(chat_messages) > 100: chat_messages.pop(0)
    return jsonify({"success": True})
