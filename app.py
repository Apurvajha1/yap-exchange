import os
from flask import Flask, render_template, request, jsonify, session
from models import db, User, Target, Contract
import json
from dotenv import load_dotenv

from admin import admin_bp
from auth import auth_bp
from chat import chat_bp

# Load the secret .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-key-do-not-use-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mutemarket.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ADMIN_USER = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASSWORD', 'admin123')

db.init_app(app)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

with app.app_context():
    db.create_all()
    # Now it spawns whatever admin is in the .env file
    if not User.query.filter_by(username=ADMIN_USER).first():
        admin = User(username=ADMIN_USER, balance=999999.0)
        admin.set_password(ADMIN_PASS)
        db.session.add(admin)
        db.session.commit()

# ... [Keep the rest of your app.py routes exactly the same] ...
