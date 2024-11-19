from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    social_login_provider = db.Column(db.String(50), nullable=False)  # Google or Facebook
    profile_picture = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scraped_data = db.relationship('ScrapedData', backref='user', lazy=True, cascade='all, delete-orphan')
    prompt_logs = db.relationship('PromptLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'social_login_provider': self.social_login_provider,
            'profile_picture': self.profile_picture,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ScrapedData(db.Model):
    __tablename__ = 'scraped_data'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url = db.Column(db.String(500), nullable=False)
    content = db.Column(JSON, nullable=False)  # Stores structured data like Name, About, Source, Industry, etc.
    page_metadata = db.Column(JSON)  # Stores title, description, etc.
    created_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScrapedData {self.url}>'

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'content': {
                'name': self.content.get('name'),
                'about': self.content.get('about'),
                'source': self.content.get('source'),
                'industry': self.content.get('industry'),
                'page_content_type': self.content.get('page_content_type'),
                'contact': self.content.get('contact'),
                'email': self.content.get('email')
            } if self.content else {},
            'metadata': self.page_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PromptLog(db.Model):
    __tablename__ = 'prompt_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_text = db.Column(db.Text, nullable=False)
    generated_output = db.Column(db.Text, nullable=False)
    tokens_used = db.Column(db.Integer)  # Added to track token usage for API costs
    created_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PromptLog {self.id}>'

    def to_dict(self):
        try:
            if isinstance(self.created_at, str):
                created_at_str = self.created_at
            else:
                created_at_str = self.created_at.isoformat() if self.created_at else None
                
            return {
                'id': self.id,
                'prompt_text': self.prompt_text,
                'generated_output': self.generated_output,
                'tokens_used': self.tokens_used,
                'created_at': created_at_str
            }
        except Exception as e:
            # Fallback if there's any issue with date conversion
            return {
                'id': self.id,
                'prompt_text': self.prompt_text,
                'generated_output': self.generated_output,
                'tokens_used': self.tokens_used,
                'created_at': str(self.created_at) if self.created_at else None
            }
