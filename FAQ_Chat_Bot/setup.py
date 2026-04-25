#!/usr/bin/env python3
"""
WhatsApp FAQ Chatbot Setup Script
This script helps with initial setup and configuration
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print("✅ Python version check passed")

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies")
        sys.exit(1)

def download_nltk_data():
    """Download required NLTK data"""
    print("📚 Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("✅ NLTK data downloaded successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not download NLTK data: {e}")

def setup_environment():
    """Setup environment configuration"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("⚙️  Creating environment file...")
        with open(env_example, 'r') as example, open(env_file, 'w') as env:
            env.write(example.read())
        print("✅ Created .env file from .env.example")
        print("📝 Please edit .env file with your configuration")
    elif env_file.exists():
        print("✅ Environment file already exists")
    else:
        print("⚠️  No .env.example file found")

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'uploads', 'backups']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Created necessary directories")

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
            print("✅ Database initialized successfully")
            
            # Check if sample data exists
            from models import FAQ
            if FAQ.query.count() == 0:
                print("📝 Adding sample FAQ data...")
                add_sample_data()
            else:
                print("✅ Sample data already exists")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

def add_sample_data():
    """Add sample FAQ data"""
    from models import FAQ
    from app import db
    
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
        },
        {
            'question': 'Do you offer international shipping?',
            'answer': 'Yes, we ship to most countries worldwide. International shipping rates and delivery times vary by destination. You can check shipping options and costs at checkout.',
            'category': 'Shipping',
            'keywords': 'international, shipping, worldwide, global'
        },
        {
            'question': 'How do I track my order?',
            'answer': 'Once your order ships, you will receive a tracking number via email. You can track your order on our website using the tracking number, or contact customer support for assistance.',
            'category': 'Orders',
            'keywords': 'track, order, tracking number, status'
        },
        {
            'question': 'What is your privacy policy?',
            'answer': 'We take your privacy seriously. We collect only necessary information to provide our services and never share your personal data with third parties without your consent. Our full privacy policy is available on our website.',
            'category': 'Legal',
            'keywords': 'privacy, policy, data, protection'
        }
    ]
    
    for faq_data in sample_faqs:
        faq = FAQ(**faq_data)
        db.session.add(faq)
    
    db.session.commit()
    print(f"✅ Added {len(sample_faqs)} sample FAQs")

def run_tests():
    """Run basic tests to verify setup"""
    print("🧪 Running basic tests...")
    try:
        # Test imports
        from app import app
        from models import FAQ, Conversation, UserSession
        from faq_manager import FAQManager
        from message_handler import MessageHandler
        
        # Test database connection
        with app.app_context():
            from app import db
            db.engine.execute('SELECT 1')
        
        print("✅ All tests passed")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print("\n1. Configure your environment:")
    print("   Edit the .env file with your Twilio credentials")
    print("\n2. Set up Twilio WhatsApp:")
    print("   • Create a Twilio account at twilio.com")
    print("   • Enable WhatsApp sandbox")
    print("   • Get your Account SID, Auth Token, and phone number")
    print("\n3. Start the application:")
    print("   python app.py")
    print("\n4. Test the bot:")
    print("   • Send a message to your WhatsApp number")
    print("   • Try commands like 'help', 'categories', or ask questions")
    print("\n5. Deploy to production:")
    print("   • Use Docker: docker-compose up")
    print("   • Or deploy to Heroku/AWS/DigitalOcean")
    print("\n📚 For detailed instructions, see README.md")
    print("\n🔗 Admin API available at: http://localhost:5000/admin/")
    print("="*60)

def main():
    """Main setup function"""
    print("🤖 WhatsApp FAQ Chatbot Setup")
    print("="*40)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Run setup steps
    check_python_version()
    install_dependencies()
    download_nltk_data()
    setup_environment()
    create_directories()
    initialize_database()
    
    if run_tests():
        print_next_steps()
    else:
        print("❌ Setup completed with errors. Please check the messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
