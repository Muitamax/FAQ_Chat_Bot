"""
Sample data generator for WhatsApp FAQ Chatbot
This script can be used to populate the database with sample FAQs
"""

from app import app, db
from models import FAQ
import json

def load_faqs_from_json():
    """Load FAQs from a JSON file"""
    faqs_data = [
        {
            "question": "What products do you offer?",
            "answer": "We offer a wide range of products including electronics, clothing, home goods, books, and more. Visit our website to browse our full catalog.",
            "category": "Products",
            "keywords": "products, catalog, items, goods"
        },
        {
            "question": "Do you have a loyalty program?",
            "answer": "Yes! Our loyalty program offers points for every purchase, exclusive discounts, and early access to sales. Sign up on our website to start earning rewards today.",
            "category": "Programs",
            "keywords": "loyalty, rewards, points, program"
        },
        {
            "question": "Can I cancel my order?",
            "answer": "Orders can be cancelled within 2 hours of placement. After that, you may need to return the item once received. Contact customer support immediately if you need to cancel.",
            "category": "Orders",
            "keywords": "cancel, order, stop, change"
        },
        {
            "question": "Do you gift wrap?",
            "answer": "Yes, we offer gift wrapping services for a small additional fee. You can select gift wrapping options at checkout and include a personalized message.",
            "category": "Services",
            "keywords": "gift, wrap, present, packaging"
        },
        {
            "question": "What is your warranty policy?",
            "answer": "Most products come with a 1-year manufacturer warranty. Extended warranties are available for purchase. Please check the product page for specific warranty information.",
            "category": "Warranty",
            "keywords": "warranty, guarantee, protection, repair"
        },
        {
            "question": "How do I create an account?",
            "answer": "Click 'Sign Up' on our website and follow the registration process. You'll need to provide your email address and create a password. Account creation is free and takes less than a minute.",
            "category": "Account",
            "keywords": "account, register, sign up, create"
        },
        {
            "question": "Can I change my order after placing it?",
            "answer": "Order changes are possible within 2 hours of placement. After that, the order enters our fulfillment process and cannot be modified. Contact support immediately if you need changes.",
            "category": "Orders",
            "keywords": "change, modify, update, order"
        },
        {
            "question": "Do you offer bulk discounts?",
            "answer": "Yes, we offer bulk discounts for orders over 10 items. Discount rates vary by quantity and product type. Contact our sales team for a custom quote.",
            "category": "Pricing",
            "keywords": "bulk, wholesale, discount, quantity"
        },
        {
            "question": "What shipping carriers do you use?",
            "answer": "We partner with UPS, FedEx, USPS, and DHL for domestic and international shipping. The carrier is selected based on your location and shipping speed preference.",
            "category": "Shipping",
            "keywords": "carrier, shipping, UPS, FedEx, USPS, DHL"
        },
        {
            "question": "How do I use a promo code?",
            "answer": "Enter your promo code in the 'Promo Code' field at checkout and click 'Apply'. The discount will be reflected in your order total. Only one promo code can be used per order.",
            "category": "Pricing",
            "keywords": "promo, code, discount, coupon"
        },
        {
            "question": "Can I ship to a different address?",
            "answer": "Yes, you can ship to any address during checkout. You can also save multiple shipping addresses in your account for future orders.",
            "category": "Shipping",
            "keywords": "address, shipping, different, location"
        },
        {
            "question": "What if my item arrives damaged?",
            "answer": "If your item arrives damaged, contact us within 48 hours with photos of the damage. We'll arrange for a replacement or full refund, including return shipping if needed.",
            "category": "Returns",
            "keywords": "damaged, broken, defective, replacement"
        },
        {
            "question": "Do you price match?",
            "answer": "We offer price matching on identical items from authorized competitors. Contact our sales team with proof of the lower price to request a price match.",
            "category": "Pricing",
            "keywords": "price match, guarantee, competitor"
        },
        {
            "question": "How secure is my payment information?",
            "answer": "We use industry-standard SSL encryption and never store your payment details on our servers. All transactions are processed through secure payment gateways.",
            "category": "Security",
            "keywords": "security, payment, encryption, safe"
        },
        {
            "question": "Can I speak to a human agent?",
            "answer": "Yes! Our human agents are available Monday-Friday 9AM-6PM. You can reach them by calling 1-800-123-4567, emailing support@example.com, or by typing 'human' in this chat.",
            "category": "Support",
            "keywords": "human, agent, person, representative"
        }
    ]
    
    return faqs_data

def add_sample_data():
    """Add sample FAQs to the database"""
    with app.app_context():
        # Check if data already exists
        if FAQ.query.count() > 0:
            print(f"Database already contains {FAQ.query.count()} FAQs")
            return
        
        faqs_data = load_faqs_from_json()
        
        for faq_data in faqs_data:
            faq = FAQ(**faq_data)
            db.session.add(faq)
        
        db.session.commit()
        print(f"Added {len(faqs_data)} sample FAQs to the database")

def export_faqs_to_json(filename='faqs_export.json'):
    """Export existing FAQs to JSON file"""
    with app.app_context():
        faqs = FAQ.query.all()
        faqs_data = [faq.to_dict() for faq in faqs]
        
        with open(filename, 'w') as f:
            json.dump(faqs_data, f, indent=2, default=str)
        
        print(f"Exported {len(faqs)} FAQs to {filename}")

def import_faqs_from_json(filename='faqs_export.json'):
    """Import FAQs from JSON file"""
    try:
        with open(filename, 'r') as f:
            faqs_data = json.load(f)
        
        with app.app_context():
            for faq_data in faqs_data:
                # Remove fields that shouldn't be imported
                faq_data.pop('id', None)
                faq_data.pop('created_at', None)
                faq_data.pop('updated_at', None)
                
                faq = FAQ(**faq_data)
                db.session.add(faq)
            
            db.session.commit()
            print(f"Imported {len(faqs_data)} FAQs from {filename}")
    
    except FileNotFoundError:
        print(f"File {filename} not found")
    except Exception as e:
        print(f"Error importing FAQs: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "add":
            add_sample_data()
        elif command == "export":
            filename = sys.argv[2] if len(sys.argv) > 2 else 'faqs_export.json'
            export_faqs_to_json(filename)
        elif command == "import":
            filename = sys.argv[2] if len(sys.argv) > 2 else 'faqs_export.json'
            import_faqs_from_json(filename)
        else:
            print("Usage: python sample_data.py [add|export|import] [filename]")
    else:
        add_sample_data()
