from datetime import datetime
from models import Conversation, UserSession, Analytics
from faq_manager import FAQManager
import json

class MessageHandler:
    """Handles incoming messages and generates responses"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.faq_manager = FAQManager(db_session)
    
    def process_message(self, incoming_msg, phone_number):
        """Process incoming message and generate response"""
        # Save incoming message
        conversation = Conversation(
            phone_number=phone_number,
            message=incoming_msg,
            message_type='incoming'
        )
        self.db.add(conversation)
        
        # Get or create user session
        session = UserSession.query.filter_by(phone_number=phone_number).first()
        if not session:
            session = UserSession(phone_number=phone_number)
            self.db.add(session)
        
        session.last_activity = datetime.utcnow()
        session.conversation_count += 1
        
        # Generate response
        response_text = self.generate_response(incoming_msg, session)
        
        # Save response
        conversation.response = response_text
        self.db.commit()
        
        # Update analytics
        self.update_analytics(session, response_text)
        
        return response_text
    
    def generate_response(self, message, session):
        """Generate appropriate response based on message and session state"""
        message_lower = message.lower().strip()
        
        # Handle feedback on previous answers
        if session.state == 'answered':
            if message_lower in ['yes', 'y', 'helpful', 'good', 'thanks', 'thank you']:
                session.state = 'welcome'
                return "Great! I'm glad I could help. Is there anything else you'd like to know?"
            elif message_lower in ['no', 'n', 'not helpful', 'wrong']:
                session.state = 'not_satisfied'
                return "I apologize that wasn't helpful. Let me try again or I can connect you with a human agent. Would you like to:\n• Try a different question\n• Speak with a human agent\n• See available categories"
        
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
        if any(agent_cmd in message_lower for agent_cmd in ['human', 'agent', 'talk to person', 'speak to human', 'real person']):
            session.state = 'human_requested'
            return "I'm connecting you with a human agent. Please wait a moment while I transfer your request. They typically respond within 5-10 minutes during business hours."
        
        # Handle specific category browsing
        if message_lower.startswith('category:') or message_lower.startswith('show:'):
            category = message_lower.replace('category:', '').replace('show:', '').strip()
            return self.get_category_faqs(category)
        
        # Search for FAQ answer
        best_faq, similarity = self.faq_manager.find_best_answer(message)
        
        if best_faq and similarity >= 0.3:
            session.state = 'answered'
            # Link the conversation to the FAQ
            latest_conversation = Conversation.query.filter_by(phone_number=session.phone_number).order_by(Conversation.timestamp.desc()).first()
            if latest_conversation:
                latest_conversation.faq_id = best_faq.id
            
            return f"📚 **{best_faq.question}**\n\n{best_faq.answer}\n\nWas this helpful? Reply with 'yes' or 'no'."
        
        # Try keyword search as fallback
        keyword_faq = self.faq_manager.search_by_keywords(message)
        if keyword_faq:
            session.state = 'answered'
            # Link the conversation to the FAQ
            latest_conversation = Conversation.query.filter_by(phone_number=session.phone_number).order_by(Conversation.timestamp.desc()).first()
            if latest_conversation:
                latest_conversation.faq_id = keyword_faq.id
            
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
• Type 'category:[name]' to see FAQs from a specific category
• Type 'human' to speak with an agent

What would you like to know?"""
    
    def get_help_message(self):
        return """📋 **Available Commands:**

• Ask any question - I'll search our FAQ database
• 'help' or 'menu' - Show this help message
• 'categories' or 'topics' - Show available FAQ categories
• 'category:[name]' - Show FAQs from specific category
• 'human' or 'agent' - Connect with a human agent
• 'hello' or 'hi' - Start over with welcome message

**Examples:**
• "What are your business hours?"
• "How do I return an item?"
• "category:Shipping"
• "human"

Feel free to ask me anything!"""
    
    def get_categories_message(self):
        categories = self.faq_manager.get_all_categories()
        if categories:
            category_list = '\n'.join([f"• {cat}" for cat in categories])
            return f"📂 **Available Categories:**\n\n{category_list}\n\nType 'category:[name]' to see FAQs from any category, or just ask me anything!"
        else:
            return "No specific categories are available at the moment. Feel free to ask any question!"
    
    def get_category_faqs(self, category_name):
        faqs = self.faq_manager.search_by_category(category_name)
        if faqs:
            faq_list = '\n\n'.join([f"**Q{i+1}:** {faq.question}" for i, faq in enumerate(faqs[:5])])
            return f"📂 **FAQs in {category_name}:**\n\n{faq_list}\n\nYou can ask me any of these questions for detailed answers!"
        else:
            return f"No FAQs found in the '{category_name}' category. Try 'categories' to see available topics."
    
    def get_not_found_message(self):
        return """❌ I couldn't find an answer to your question.

Here are some options:
• Try rephrasing your question differently
• Type 'categories' to see available topics
• Type 'help' for assistance
• Type 'human' to speak with an agent

**Suggestions:**
• Be specific about what you want to know
• Use simple, clear language
• Try related keywords

I'm always learning, so your question helps improve my knowledge!"""
    
    def update_analytics(self, session, response_text):
        """Update daily analytics"""
        today = datetime.utcnow().date()
        analytics = Analytics.query.filter_by(date=today).first()
        
        if not analytics:
            analytics = Analytics(date=today)
            self.db.add(analytics)
        
        analytics.total_conversations += 1
        
        # Check if this is a new user today
        today_conversations = Conversation.query.filter(
            Conversation.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).filter_by(phone_number=session.phone_number).count()
        
        if today_conversations == 1:
            analytics.unique_users += 1
        
        # Check if response was successful
        if '❌' not in response_text and 'couldn\'t find' not in response_text.lower():
            analytics.successful_responses += 1
        else:
            analytics.failed_responses += 1
        
        # Check for human agent request
        if 'human agent' in response_text.lower():
            analytics.human_agent_requests += 1
        
        self.db.commit()
    
    def get_conversation_history(self, phone_number, limit=10):
        """Get conversation history for a user"""
        conversations = Conversation.query.filter_by(phone_number=phone_number).order_by(Conversation.timestamp.desc()).limit(limit).all()
        return [conv.to_dict() for conv in conversations]
    
    def get_user_session(self, phone_number):
        """Get current user session"""
        return UserSession.query.filter_by(phone_number=phone_number).first()
    
    def reset_session(self, phone_number):
        """Reset user session"""
        session = UserSession.query.filter_by(phone_number=phone_number).first()
        if session:
            session.state = 'welcome'
            self.db.commit()
        return session
