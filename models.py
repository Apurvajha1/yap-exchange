from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Float, default=1000.0)
    last_allowance_date = db.Column(db.String(20), default="")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    odds_json = db.Column(db.Text, nullable=False)
    total_wagered = db.Column(db.Float, default=0.0)

    # NEW: Tracks how many times they've been hit with the Banhammer
    times_muted = db.Column(db.Integer, default=0)

    def get_odds(self):
        return json.loads(self.odds_json)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    target_name = db.Column(db.String(80), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    stake = db.Column(db.Float, nullable=False)
    potential_payout = db.Column(db.Float, nullable=False)
