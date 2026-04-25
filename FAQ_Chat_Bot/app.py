from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
import re
from datetime import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Download NLTK data (only need to do this once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///faq_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Twilio client
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

# Models
class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(20), default='incoming')

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    state = db.Column(db.String(50), default='welcome')
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_count = db.Column(db.Integer, default=0)

# FAQ Manager
class FAQManager:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.faqs = []
        self.load_faqs()
    
    def load_faqs(self):
        """Load all active FAQs from database"""
        self.faqs = FAQ.query.filter_by(is_active=True).all()
        if self.faqs:
            questions = [faq.question for faq in self.faqs]
            self.tfidf_matrix = self.vectorizer.fit_transform(questions)
        else:
            self.tfidf_matrix = None
    
    def find_best_answer(self, user_question, threshold=0.3):
        """Find the best matching FAQ using cosine similarity"""
        if not self.faqs or self.tfidf_matrix is None:
            return None, 0.0
        
        # Transform user question
        user_vector = self.vectorizer.transform([user_question])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(user_vector, self.tfidf_matrix)
        max_similarity = np.max(similarities)
        best_index = np.argmax(similarities)
        
        if max_similarity >= threshold:
            return self.faqs[best_index], max_similarity
        return None, max_similarity
    
    def search_by_keywords(self, user_question):
        """Search FAQs by keywords"""
        user_tokens = set(word.lower() for word in word_tokenize(user_question.lower()))
        user_tokens.discard('?'')
        
        best_matches = []
        for faq in self.faqs:
            faq_tokens = set(word.lower() for word in word_tokenize(faq.question.lower()))
            faq_tokens.update(word.lower() for word in word_tokenize(faq.answer.lower()))
            
            # Check keywords field if available
            if faq.keywords:
                faq_tokens.update(word.lower() for word in faq.keywords.lower().split(','))
            
            # Calculate keyword overlap
            overlap = len(user_tokens.intersection(faq_tokens))
            if overlap > 0:
                best_matches.append((faq, overlap))
        
        # Sort by overlap count and return best match
        if best_matches:
            best_matches.sort(key=lambda x: x[1], reverse=True)
            return best_matches[0][0]
        return None

# Message Handler
class MessageHandler:
    def __init__(self):
        self.faq_manager = FAQManager()
    
    def process_message(self, incoming_msg, phone_number):
        """Process incoming message and generate response"""
        # Save incoming message
        conversation = Conversation(
            phone_number=phone_number,
            message=incoming_msg,
            message_type='incoming'
        )
        db.session.add(conversation)
        
        # Get or create user session
        session = UserSession.query.filter_by(phone_number=phone_number).first()
        if not session:
            session = UserSession(phone_number=phone_number)
            db.session.add(session)
        
        session.last_activity = datetime.utcnow()
        session.conversation_count += 1
        
        # Generate response
        response_text = self.generate_response(incoming_msg, session)
        
        # Save response
        conversation.response = response_text
        db.session.commit()
        
        return response_text
    
    def generate_response(self, message, session):
        """Generate appropriate response based on message and session state"""
        message_lower = message.lower().strip()
        
        # Handle greetings
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            session.state = 'welcome'
            return self.get_welcome_message()
        
        # Handle help commands
        if any(help_cmd in message_lower for help_cmd in ['help', 'menu', 'options', 'commands']):
            return self.get_help_message()
        
        # Handle category requests
        if 'categories' in message_lower or 'topics' in message_lower:
            return self.get_categories_message()
        
        # Handle human agent request
        if any(agent_cmd in message_lower for agent_cmd in ['human', 'agent', 'talk to person', 'speak to human']):
            session.state = 'human_requested'
            return "I'm connecting you with a human agent. Please wait a moment while I transfer your request."
        
        # Search for FAQ answer
        best_faq, similarity = self.faq_manager.find_best_answer(message)
        
        if best_faq and similarity >= 0.3:
            session.state = 'answered'
            return f"📚 **{best_faq.question}**\n\n{best_faq.answer}\n\nWas this helpful? Reply with 'yes' or 'no'."
        
        # Try keyword search as fallback
        keyword_faq = self.faq_manager.search_by_keywords(message)
        if keyword_faq:
            session.state = 'answered'
            return f"🔍 **Found related information:**\n\n**{keyword_faq.question}**\n\n{keyword_faq.answer}\n\nWas this helpful? Reply with 'yes' or 'no'."
        
        # No answer found
        session.state = 'not_found'
        return self.get_not_found_message()
    
    def get_welcome_message(self):
        return """🤖 Welcome to our FAQ Chatbot!

I'm here to help you find answers to frequently asked questions.

You can:
• Ask me any question about our products/services
• Type 'help' to see all commands
• Type 'categories' to see available topics
• Type 'human' to speak with an agent

What would you like to know?"""
    
    def get_help_message(self):
        return """📋 **Available Commands:**

• Ask any question - I'll search our FAQ database
• 'help' or 'menu' - Show this help message
• 'categories' or 'topics' - Show available FAQ categories
• 'human' or 'agent' - Connect with a human agent
• 'hello' or 'hi' - Start over with welcome message

Feel free to ask me anything!"""
    
    def get_categories_message(self):
        categories = db.session.query(FAQ.category).filter_by(is_active=True).distinct().all()
        if categories:
            category_list = '\n'.join([f"• {cat[0]}" for cat in categories if cat[0]])
            return f"📂 **Available Categories:**\n\n{category_list}\n\nYou can ask me about any of these topics!"
        else:
            return "No specific categories are available at the moment. Feel free to ask any question!"
    
    def get_not_found_message(self):
        return """❌ I couldn't find an answer to your question.

Here are some options:
• Try rephrasing your question
• Type 'categories' to see available topics
• Type 'help' for assistance
• Type 'human' to speak with an agent

I'm always learning, so your question helps improve my knowledge!"""

# Initialize message handler
message_handler = MessageHandler()

# Routes
@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'message': 'WhatsApp FAQ Chatbot is running'
    })

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '').replace('whatsapp:', '')
    
    if not incoming_msg:
        return "No message received", 400
    
    # Process message and get response
    response_text = message_handler.process_message(incoming_msg, sender_phone)
    
    # Create Twilio response
    response = MessagingResponse()
    response.message(response_text)
    
    return str(response)

@app.route('/admin/faqs', methods=['GET'])
def get_faqs():
    """Get all FAQs (for admin interface)"""
    faqs = FAQ.query.all()
    return jsonify([{
        'id': faq.id,
        'question': faq.question,
        'answer': faq.answer,
        'category': faq.category,
        'keywords': faq.keywords,
        'is_active': faq.is_active,
        'created_at': faq.created_at.isoformat()
    } for faq in faqs])

@app.route('/admin/faqs', methods=['POST'])
def add_faq():
    """Add a new FAQ"""
    data = request.get_json()
    
    if not data or 'question' not in data or 'answer' not in data:
        return jsonify({'error': 'Question and answer are required'}), 400
    
    faq = FAQ(
        question=data['question'],
        answer=data['answer'],
        category=data.get('category'),
        keywords=data.get('keywords')
    )
    
    db.session.add(faq)
    db.session.commit()
    
    # Reload FAQs in memory
    message_handler.faq_manager.load_faqs()
    
    return jsonify({'message': 'FAQ added successfully', 'id': faq.id}), 201

@app.route('/admin/faqs/<int:faq_id>', methods=['PUT'])
def update_faq(faq_id):
    """Update an existing FAQ"""
    faq = FAQ.query.get_or_404(faq_id)
    data = request.get_json()
    
    if 'question' in data:
        faq.question = data['question']
    if 'answer' in data:
        faq.answer = data['answer']
    if 'category' in data:
        faq.category = data['category']
    if 'keywords' in data:
        faq.keywords = data['keywords']
    if 'is_active' in data:
        faq.is_active = data['is_active']
    
    faq.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Reload FAQs in memory
    message_handler.faq_manager.load_faqs()
    
    return jsonify({'message': 'FAQ updated successfully'})

@app.route('/admin/faqs/<int:faq_id>', methods=['DELETE'])
def delete_faq(faq_id):
    """Delete an FAQ"""
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    
    # Reload FAQs in memory
    message_handler.faq_manager.load_faqs()
    
    return jsonify({'message': 'FAQ deleted successfully'})

@app.route('/admin/conversations', methods=['GET'])
def get_conversations():
    """Get conversation history"""
    conversations = Conversation.query.order_by(Conversation.timestamp.desc()).limit(100).all()
    return jsonify([{
        'id': conv.id,
        'phone_number': conv.phone_number,
        'message': conv.message,
        'response': conv.response,
        'timestamp': conv.timestamp.isoformat(),
        'message_type': conv.message_type
    } for conv in conversations])

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Add sample FAQs if database is empty
    if FAQ.query.count() == 0:
        sample_faqs = [
            {
                'question': 'What are your business hours?',
                'answer': 'We are open Monday through Friday, 9:00 AM to 6:00 PM. We are closed on weekends and public holidays.',
                'category': 'General',
                'keywords': 'hours, timing, schedule, open'
            },
            {
                'question': 'How can I contact customer support?',
                'answer': 'You can reach our customer support team via:\n• Phone: 1-800-123-4567\n• Email: support@example.com\n• Live chat on our website\n• WhatsApp: +1-234-567-8900',
                'category': 'Contact',
                'keywords': 'contact, support, phone, email, help'
            },
            {
                'question': 'What payment methods do you accept?',
                'answer': 'We accept the following payment methods:\n• Credit/Debit cards (Visa, MasterCard, American Express)\n• PayPal\n• Bank transfers\n• Mobile payment apps\n• Cash on delivery (for eligible orders)',
                'category': 'Payment',
                'keywords': 'payment, methods, cards, paypal, bank'
            },
            {
                'question': 'How long does shipping take?',
                'answer': 'Shipping times vary by location:\n• Standard shipping: 5-7 business days\n• Express shipping: 2-3 business days\n• Overnight shipping: 1 business day\nInternational orders may take 10-15 business days.',
                'category': 'Shipping',
                'keywords': 'shipping, delivery, time, how long'
            },
            {
                'question': 'What is your return policy?',
                'answer': 'We offer a 30-day return policy. Items must be unused and in original packaging. To initiate a return, contact our customer service or use the return portal on our website. Refunds are processed within 5-7 business days after we receive the returned item.',
                'category': 'Returns',
                'keywords': 'return, refund, policy, exchange'
            }
        ]
        
        for faq_data in sample_faqs:
            faq = FAQ(**faq_data)
            db.session.add(faq)
        
        db.session.commit()
        message_handler.faq_manager.load_faqs()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Load FAQs after creating tables
        message_handler.faq_manager.load_faqs()
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
