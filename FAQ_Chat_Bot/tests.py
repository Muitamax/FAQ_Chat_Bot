import unittest
from app import app, db, message_handler
from models import FAQ, Conversation, UserSession
from faq_manager import FAQManager
import json
from datetime import datetime

class TestFAQChatbot(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Add test FAQs
            test_faqs = [
                FAQ(
                    question="What are your business hours?",
                    answer="We are open 9 AM to 6 PM, Monday to Friday.",
                    category="General",
                    keywords="hours, timing, schedule"
                ),
                FAQ(
                    question="How do I contact support?",
                    answer="You can email support@example.com or call 1-800-123-4567.",
                    category="Contact",
                    keywords="contact, support, email, phone"
                )
            ]
            
            for faq in test_faqs:
                db.session.add(faq)
            
            db.session.commit()
            message_handler.faq_manager.load_faqs()
    
    def tearDown(self):
        """Clean up test environment"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'running')
    
    def test_add_faq(self):
        """Test adding a new FAQ"""
        faq_data = {
            'question': 'Test question?',
            'answer': 'Test answer.',
            'category': 'Test',
            'keywords': 'test, question'
        }
        
        response = self.client.post('/admin/faqs',
                                   data=json.dumps(faq_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'FAQ added successfully')
    
    def test_get_faqs(self):
        """Test retrieving all FAQs"""
        response = self.client.get('/admin/faqs')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreater(len(data), 0)  # Should have test FAQs
    
    def test_message_processing(self):
        """Test message processing logic"""
        with app.app_context():
            # Test greeting
            response = message_handler.process_message("Hello", "+1234567890")
            self.assertIn("Welcome", response)
            
            # Test FAQ matching
            response = message_handler.process_message("What are your hours?", "+1234567890")
            self.assertIn("9 AM to 6 PM", response)
            
            # Test help command
            response = message_handler.process_message("help", "+1234567890")
            self.assertIn("Available Commands", response)
    
    def test_faq_search(self):
        """Test FAQ search functionality"""
        with app.app_context():
            faq_manager = FAQManager(db.session)
            
            # Test exact match
            faq, similarity = faq_manager.find_best_answer("business hours")
            self.assertIsNotNone(faq)
            self.assertGreater(similarity, 0.3)
            
            # Test keyword search
            faq = faq_manager.search_by_keywords("contact support")
            self.assertIsNotNone(faq)
    
    def test_conversation_tracking(self):
        """Test conversation tracking"""
        with app.app_context():
            # Process a message
            message_handler.process_message("Hello", "+1234567890")
            
            # Check conversation was saved
            conversation = Conversation.query.filter_by(phone_number="+1234567890").first()
            self.assertIsNotNone(conversation)
            self.assertEqual(conversation.message, "Hello")
            
            # Check user session was created
            session = UserSession.query.filter_by(phone_number="+1234567890").first()
            self.assertIsNotNone(session)
            self.assertEqual(session.conversation_count, 1)
    
    def test_whatsapp_webhook(self):
        """Test WhatsApp webhook endpoint"""
        # Mock WhatsApp message data
        webhook_data = {
            'Body': 'Hello',
            'From': 'whatsapp:+1234567890'
        }
        
        response = self.client.post('/webhook/whatsapp', data=webhook_data)
        
        # Should return TwiML response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<?xml', response.data)  # TwiML XML
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        response = self.client.get('/admin/categories')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreater(len(data), 0)  # Should have test categories

class TestFAQManager(unittest.TestCase):
    
    def setUp(self):
        """Set up FAQ manager tests"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            self.faq_manager = FAQManager(db.session)
            
            # Add test FAQ
            faq = FAQ(
                question="How to return items?",
                answer="Return within 30 days with original packaging.",
                category="Returns",
                keywords="return, refund, exchange"
            )
            db.session.add(faq)
            db.session.commit()
            self.faq_manager.load_faqs()
    
    def tearDown(self):
        """Clean up FAQ manager tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_preprocess_text(self):
        """Test text preprocessing"""
        text = "Hello! How are you? 123"
        processed = self.faq_manager.preprocess_text(text)
        self.assertEqual(processed, "hello how are you 123")
    
    def test_keyword_extraction(self):
        """Test keyword extraction"""
        from utils import extract_keywords
        keywords = extract_keywords("What are your business hours and payment methods?")
        expected = ['business', 'hours', 'payment', 'methods']
        self.assertTrue(any(k in keywords for k in expected))
    
    def test_similarity_calculation(self):
        """Test similarity calculation"""
        from utils import calculate_similarity
        similarity = calculate_similarity("business hours", "operating hours")
        self.assertGreater(similarity, 0.5)
        
        similarity = calculate_similarity("business hours", "return policy")
        self.assertLess(similarity, 0.3)

if __name__ == '__main__':
    unittest.main()
