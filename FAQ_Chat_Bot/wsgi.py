from app import app, db, message_handler

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Load FAQs after creating tables
        message_handler.faq_manager.load_faqs()
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
