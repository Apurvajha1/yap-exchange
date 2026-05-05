import os
from flask import Flask, render_template, request, jsonify, session
from models import db, User, Target, Contract
import json
from dotenv import load_dotenv

from admin import admin_bp
from auth import auth_bp
from chat import chat_bp

# Load the secret .env file so GitHub bots don't steal your passwords
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-key-do-not-use-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mutemarket.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Pull the admin credentials from your invisible .env file
ADMIN_USER = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASSWORD', 'admin123')

db.init_app(app)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

with app.app_context():
    db.create_all()
    # Spawns the boss account dynamically using your secure environment variables
    if not User.query.filter_by(username=ADMIN_USER).first():
        admin = User(username=ADMIN_USER, balance=999999.0)
        admin.set_password(ADMIN_PASS)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/targets', methods=['GET', 'POST'])
def handle_targets():
    if request.method == 'GET':
        targets = Target.query.all()
        # Sends total_wagered so the frontend can sort the "Top 4" tab
        return jsonify([{"id": t.id, "name": t.name, "odds": t.get_odds(), "total_wagered": t.total_wagered} for t in targets])

    if request.method == 'POST':
        data = request.json
        # Check if the target is already on the board (case-insensitive blocker)
        existing = Target.query.filter(db.func.lower(Target.name) == db.func.lower(data['name'])).first()
        if existing:
            return jsonify({"success": False, "message": "Bro is already on the hit list!"}), 400

        # The server automatically generates the initial baseline odds with the 1w option
        initial_odds = {"1h": 3.0, "24h": 5.0, "1w": 8.0}

        new_target = Target(name=data['name'], odds_json=json.dumps(initial_odds))
        db.session.add(new_target)
        db.session.commit()
        return jsonify({"success": True})

@app.route('/api/bet', methods=['POST'])
def place_bet():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    stake = float(data['stake'])
    user = User.query.get(session['user_id'])

    if user.balance < stake: return jsonify({"success": False, "message": "Not enough 💊"}), 400
    user.balance -= stake

    target = Target.query.filter_by(name=data['target']['name']).first()
    if target:
        target.total_wagered += stake

        # --- DYNAMIC PARI-MUTUEL ODDS LOGIC ---
        current_odds = json.loads(target.odds_json)
        chosen_dur = data['target']['dur']

        # Math: Larger bets cause a sharper drop in odds.
        decay_factor = 500.0 / (500.0 + stake)
        growth_factor = 1.0 + (stake / 2000.0)

        for dur in current_odds:
            if dur == chosen_dur:
                # Decrease odds for the heavily bet option (Minimum 1.05x)
                current_odds[dur] = max(1.05, round(current_odds[dur] * decay_factor, 2))
            else:
                # Increase odds for the neglected options (Maximum 50.0x)
                current_odds[dur] = min(50.0, round(current_odds[dur] * growth_factor, 2))

        target.odds_json = json.dumps(current_odds)
        # --------------------------------------

    new_contract = Contract(
        user_id=user.id, target_name=data['target']['name'],
        duration=data['target']['dur'], stake=stake, potential_payout=stake * float(data['target']['mult'])
    )
    db.session.add(new_contract)
    db.session.commit()
    return jsonify({"success": True, "new_balance": user.balance})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    users = User.query.filter(User.username != ADMIN_USER).order_by(User.balance.desc()).limit(5).all()
    return jsonify([{"username": u.username, "balance": u.balance} for u in users])

@app.route('/api/hot_targets', methods=['GET'])
def get_hot_targets():
    hot = Target.query.filter(Target.total_wagered > 0).order_by(Target.total_wagered.desc()).limit(5).all()
    return jsonify([{"name": t.name, "total_wagered": t.total_wagered} for t in hot])

if __name__ == '__main__':
    app.run(debug=True)
