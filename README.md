# WhatsApp FAQ Chatbot

A comprehensive WhatsApp chatbot solution for handling customer frequently asked questions (FAQs) with intelligent matching, conversation tracking, and admin interface.

## Features

- **WhatsApp Integration**: Uses Twilio WhatsApp API for seamless messaging
- **Intelligent FAQ Matching**: TF-IDF vectorization and cosine similarity for accurate answers
- **Keyword Search**: Fallback keyword matching for better coverage
- **Conversation History**: Track all user interactions
- **User Sessions**: Maintain conversation state and context
- **Admin Interface**: REST API for managing FAQs and viewing analytics
- **Analytics Dashboard**: Track bot performance and user engagement
- **Multi-language Support**: Extensible for multiple languages
- **Human Agent Handoff**: Escalate to human agents when needed

## Project Structure

```
FAQ_Chat_Bot/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── faq_manager.py        # FAQ search and matching logic
├── message_handler.py    # Message processing and response generation
├── admin.py              # Admin API endpoints
├── wsgi.py               # WSGI entry point
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Twilio account with WhatsApp enabled
- Web server (for production deployment)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///faq_bot.db

# WhatsApp Configuration
WEBHOOK_URL=https://your-domain.com/webhook/whatsapp
```

### 4. Twilio WhatsApp Setup

1. **Create a Twilio Account**: Sign up at [twilio.com](https://twilio.com)
2. **Enable WhatsApp Sandbox**: 
   - Go to Twilio Console → Messaging → Try it out → WhatsApp
   - Follow the instructions to set up the WhatsApp sandbox
3. **Get Your Credentials**: 
   - Account SID and Auth Token from Twilio Console
   - Phone number from WhatsApp sandbox settings

### 5. Database Initialization

The application will automatically create the database and tables on first run. Sample FAQs will be added automatically if the database is empty.

### 6. Run the Application

**Development:**
```bash
python app.py
```

**Production:**
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
```

### 7. Configure Webhook

1. **Deploy your application** to a web server (Heroku, AWS, DigitalOcean, etc.)
2. **Set the webhook URL** in your Twilio WhatsApp settings:
   - URL: `https://your-domain.com/webhook/whatsapp`
   - Method: POST
3. **Test the webhook** by sending a message to your WhatsApp number

## Usage

### For Customers

Customers can interact with the bot by sending messages to your WhatsApp number:

- **Ask questions**: "What are your business hours?"
- **Get help**: Send "help" or "menu"
- **Browse categories**: Send "categories" or "category:Shipping"
- **Human agent**: Send "human" or "agent"

### For Administrators

Use the admin API to manage FAQs and view analytics:

#### Add FAQ
```bash
curl -X POST http://localhost:5000/admin/faqs \
  -H "Content-Type: application/json" \
  -d '{"question": "What is your return policy?", "answer": "30-day return policy", "category": "Returns"}'
```

#### Get All FAQs
```bash
curl http://localhost:5000/admin/faqs
```

#### View Analytics
```bash
curl http://localhost:5000/admin/analytics/summary
```

#### View Conversations
```bash
curl http://localhost:5000/admin/conversations
```

## API Endpoints

### WhatsApp Webhook
- `POST /webhook/whatsapp` - Receive WhatsApp messages

### Admin API
- `GET /admin/faqs` - List all FAQs
- `POST /admin/faqs` - Add new FAQ
- `PUT /admin/faqs/{id}` - Update FAQ
- `DELETE /admin/faqs/{id}` - Delete FAQ
- `GET /admin/conversations` - View conversation history
- `GET /admin/users` - View user sessions
- `GET /admin/analytics` - View analytics data
- `GET /admin/categories` - List FAQ categories
- `GET /admin/search?q=query` - Search FAQs and conversations

## Deployment Guide

### Heroku Deployment

1. **Create Heroku App**:
```bash
heroku create your-app-name
```

2. **Set Environment Variables**:
```bash
heroku config:set TWILIO_ACCOUNT_SID=your_sid
heroku config:set TWILIO_AUTH_TOKEN=your_token
heroku config:set TWILIO_PHONE_NUMBER=your_number
heroku config:set SECRET_KEY=your_secret
```

3. **Deploy**:
```bash
git add .
git commit -m "Initial deploy"
git push heroku main
```

4. **Set Webhook**:
Update your Twilio webhook URL to: `https://your-app-name.herokuapp.com/webhook/whatsapp`

### Docker Deployment

1. **Create Dockerfile**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]
```

2. **Build and Run**:
```bash
docker build -t whatsapp-faq-bot .
docker run -p 5000:5000 --env-file .env whatsapp-faq-bot
```

## Customization

### Adding New Languages

1. Update the `preprocess_text` method in `faq_manager.py`
2. Add language-specific stop words
3. Update welcome and help messages in `message_handler.py`

### Custom Response Logic

Modify the `generate_response` method in `message_handler.py` to add:
- New command handlers
- Custom conversation flows
- Integration with external APIs

### Database Customization

For production, consider switching from SQLite to PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost/faq_bot
```

## Monitoring and Maintenance

### Health Checks

- `GET /admin/health` - Application health status
- Monitor database connectivity and FAQ count

### Analytics Tracking

The bot automatically tracks:
- Daily conversation counts
- Unique users
- Response success rates
- Human agent requests

### Backup and Recovery

- Regular database backups
- FAQ export/import functionality
- Conversation history retention policies

## Security Considerations

- Use HTTPS for webhook URLs
- Validate incoming requests from Twilio
- Secure admin endpoints with authentication
- Rate limiting for API endpoints
- Regular security updates for dependencies

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving Messages**
   - Check webhook URL is accessible
   - Verify Twilio configuration
   - Check server logs

2. **FAQ Matching Not Working**
   - Ensure FAQs are loaded in database
   - Check similarity threshold in config
   - Review FAQ content and keywords

3. **Database Connection Issues**
   - Verify DATABASE_URL configuration
   - Check database permissions
   - Ensure database server is running

### Debug Mode

Enable debug logging:
```env
FLASK_ENV=development
FLASK_DEBUG=1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Note**: This chatbot is designed to handle FAQs and basic customer inquiries. For complex customer service needs, consider integrating with a full customer service platform or human agent system.
