from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    social_login_provider = db.Column(db.String(50), nullable=False)
    profile_picture = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    scraped_data = db.relationship('ScrapedData', backref='user', lazy=True)
    prompt_logs = db.relationship('PromptLog', backref='user', lazy=True)

class ScrapedData(db.Model):
    __tablename__ = 'scraped_data'
    
    id = db.Column(db.String(255), primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    content = db.Column(JSON, nullable=False)
    page_metadata = db.Column(JSON)
    created_by_user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PromptLog(db.Model):
    __tablename__ = 'prompt_logs'
    
    id = db.Column(db.String(255), primary_key=True)
    prompt_text = db.Column(db.Text, nullable=False)
    generated_output = db.Column(db.Text, nullable=False)
    tokens_used = db.Column(db.Integer)
    created_by_user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

