from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class FAQ(db.Model):
    """FAQ model for storing frequently asked questions"""
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

class Conversation(db.Model):
    """Conversation model for storing chat history"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(20), default='incoming')  # incoming, outgoing
    faq_id = db.Column(db.Integer, db.ForeignKey('faq.id'), nullable=True)
    
    # Relationship
    faq = db.relationship('FAQ', backref='conversations')

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'message': self.message,
            'response': self.response,
            'timestamp': self.timestamp.isoformat(),
            'message_type': self.message_type,
            'faq_id': self.faq_id
        }

class UserSession(db.Model):
    """User session model for tracking user state"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    state = db.Column(db.String(50), default='welcome')
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_count = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default='en')
    preferences = db.Column(db.Text, nullable=True)  # JSON string for preferences

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'state': self.state,
            'last_activity': self.last_activity.isoformat(),
            'conversation_count': self.conversation_count,
            'language': self.language,
            'preferences': self.preferences
        }

class Analytics(db.Model):
    """Analytics model for tracking bot performance"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_conversations = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    successful_responses = db.Column(db.Integer, default=0)
    failed_responses = db.Column(db.Integer, default=0)
    human_agent_requests = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_conversations': self.total_conversations,
            'unique_users': self.unique_users,
            'successful_responses': self.successful_responses,
            'failed_responses': self.failed_responses,
            'human_agent_requests': self.human_agent_requests
        }
