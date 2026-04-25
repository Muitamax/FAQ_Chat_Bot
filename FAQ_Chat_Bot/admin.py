from flask import Blueprint, request, jsonify
from models import FAQ, Conversation, UserSession, Analytics
from faq_manager import FAQManager
from datetime import datetime, timedelta
import json

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/faqs', methods=['GET'])
def get_faqs():
    """Get all FAQs with optional filtering"""
    category = request.args.get('category')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    query = FAQ.query
    if category:
        query = query.filter_by(category=category)
    if active_only:
        query = query.filter_by(is_active=True)
    
    faqs = query.order_by(FAQ.created_at.desc()).all()
    return jsonify([faq.to_dict() for faq in faqs])

@admin_bp.route('/faqs', methods=['POST'])
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
    
    from app import db
    db.session.add(faq)
    db.session.commit()
    
    return jsonify({'message': 'FAQ added successfully', 'faq': faq.to_dict()}), 201

@admin_bp.route('/faqs/<int:faq_id>', methods=['GET'])
def get_faq(faq_id):
    """Get a specific FAQ"""
    faq = FAQ.query.get_or_404(faq_id)
    return jsonify(faq.to_dict())

@admin_bp.route('/faqs/<int:faq_id>', methods=['PUT'])
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
    
    from app import db
    db.session.commit()
    
    return jsonify({'message': 'FAQ updated successfully', 'faq': faq.to_dict()})

@admin_bp.route('/faqs/<int:faq_id>', methods=['DELETE'])
def delete_faq(faq_id):
    """Delete an FAQ"""
    faq = FAQ.query.get_or_404(faq_id)
    
    from app import db
    db.session.delete(faq)
    db.session.commit()
    
    return jsonify({'message': 'FAQ deleted successfully'})

@admin_bp.route('/faqs/bulk', methods=['POST'])
def bulk_add_faqs():
    """Add multiple FAQs at once"""
    data = request.get_json()
    
    if not data or 'faqs' not in data:
        return jsonify({'error': 'FAQs array is required'}), 400
    
    added_faqs = []
    errors = []
    
    from app import db
    for i, faq_data in enumerate(data['faqs']):
        try:
            if 'question' not in faq_data or 'answer' not in faq_data:
                errors.append(f"FAQ {i+1}: Question and answer are required")
                continue
            
            faq = FAQ(
                question=faq_data['question'],
                answer=faq_data['answer'],
                category=faq_data.get('category'),
                keywords=faq_data.get('keywords')
            )
            
            db.session.add(faq)
            added_faqs.append(faq.to_dict())
        except Exception as e:
            errors.append(f"FAQ {i+1}: {str(e)}")
    
    db.session.commit()
    
    return jsonify({
        'message': f'Added {len(added_faqs)} FAQs successfully',
        'added_faqs': added_faqs,
        'errors': errors
    })

@admin_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get conversation history with filtering options"""
    phone_number = request.args.get('phone_number')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = Conversation.query
    
    if phone_number:
        query = query.filter_by(phone_number=phone_number)
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(Conversation.timestamp >= date_from_dt)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format'}), 400
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(Conversation.timestamp <= date_to_dt)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format'}), 400
    
    conversations = query.order_by(Conversation.timestamp.desc()).offset(offset).limit(limit).all()
    
    return jsonify({
        'conversations': [conv.to_dict() for conv in conversations],
        'total': query.count(),
        'limit': limit,
        'offset': offset
    })

@admin_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation"""
    conversation = Conversation.query.get_or_404(conversation_id)
    return jsonify(conversation.to_dict())

@admin_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users with their sessions"""
    users = UserSession.query.order_by(UserSession.last_activity.desc()).all()
    return jsonify([user.to_dict() for user in users])

@admin_bp.route('/users/<phone_number>', methods=['GET'])
def get_user(phone_number):
    """Get specific user details and conversation history"""
    session = UserSession.query.filter_by(phone_number=phone_number).first_or_404()
    conversations = Conversation.query.filter_by(phone_number=phone_number).order_by(Conversation.timestamp.desc()).limit(50).all()
    
    return jsonify({
        'session': session.to_dict(),
        'conversations': [conv.to_dict() for conv in conversations]
    })

@admin_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data with date range filtering"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Analytics.query
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00')).date()
            query = query.filter(Analytics.date >= date_from_dt)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format'}), 400
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00')).date()
            query = query.filter(Analytics.date <= date_to_dt)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format'}), 400
    
    analytics = query.order_by(Analytics.date.desc()).all()
    
    # Calculate totals
    totals = {
        'total_conversations': sum(a.total_conversations for a in analytics),
        'total_unique_users': sum(a.unique_users for a in analytics),
        'total_successful_responses': sum(a.successful_responses for a in analytics),
        'total_failed_responses': sum(a.failed_responses for a in analytics),
        'total_human_agent_requests': sum(a.human_agent_requests for a in analytics)
    }
    
    return jsonify({
        'analytics': [a.to_dict() for a in analytics],
        'totals': totals,
        'success_rate': (totals['total_successful_responses'] / max(totals['total_conversations'], 1)) * 100
    })

@admin_bp.route('/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Get analytics summary for different time periods"""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    def get_period_stats(start_date, end_date):
        analytics = Analytics.query.filter(
            Analytics.date >= start_date,
            Analytics.date <= end_date
        ).all()
        
        return {
            'conversations': sum(a.total_conversations for a in analytics),
            'unique_users': sum(a.unique_users for a in analytics),
            'successful_responses': sum(a.successful_responses for a in analytics),
            'failed_responses': sum(a.failed_responses for a in analytics),
            'human_agent_requests': sum(a.human_agent_requests for a in analytics)
        }
    
    return jsonify({
        'today': get_period_stats(today, today),
        'yesterday': get_period_stats(yesterday, yesterday),
        'last_7_days': get_period_stats(week_ago, today),
        'last_30_days': get_period_stats(month_ago, today)
    })

@admin_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all FAQ categories with counts"""
    from app import db
    categories = db.session.query(
        FAQ.category,
        db.func.count(FAQ.id).label('count')
    ).filter_by(is_active=True).group_by(FAQ.category).all()
    
    return jsonify([
        {'category': cat[0] or 'Uncategorized', 'count': cat[1]}
        for cat in categories
    ])

@admin_bp.route('/search', methods=['GET'])
def search():
    """Search across conversations and FAQs"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')  # all, faqs, conversations
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    results = {'faqs': [], 'conversations': []}
    
    if search_type in ['all', 'faqs']:
        faqs = FAQ.query.filter(
            db.or_(
                FAQ.question.contains(query),
                FAQ.answer.contains(query),
                FAQ.keywords.contains(query),
                FAQ.category.contains(query)
            )
        ).filter_by(is_active=True).all()
        
        results['faqs'] = [faq.to_dict() for faq in faqs]
    
    if search_type in ['all', 'conversations']:
        conversations = Conversation.query.filter(
            db.or_(
                Conversation.message.contains(query),
                Conversation.response.contains(query)
            )
        ).limit(50).all()
        
        results['conversations'] = [conv.to_dict() for conv in conversations]
    
    return jsonify(results)

@admin_bp.route('/export', methods=['GET'])
def export_data():
    """Export data in various formats"""
    export_type = request.args.get('type', 'faqs')  # faqs, conversations, analytics
    format_type = request.args.get('format', 'json')  # json, csv
    
    if export_type == 'faqs':
        data = [faq.to_dict() for faq in FAQ.query.all()]
    elif export_type == 'conversations':
        data = [conv.to_dict() for conv in Conversation.query.limit(1000).all()]
    elif export_type == 'analytics':
        data = [a.to_dict() for a in Analytics.query.all()]
    else:
        return jsonify({'error': 'Invalid export type'}), 400
    
    if format_type == 'json':
        return jsonify(data)
    elif format_type == 'csv':
        # Simple CSV export (you might want to use a proper CSV library)
        if data:
            headers = list(data[0].keys())
            csv_lines = [','.join(headers)]
            for item in data:
                csv_lines.append(','.join(str(item.get(h, '')) for h in headers))
            return '\n'.join(csv_lines)
        else:
            return 'No data to export'
    else:
        return jsonify({'error': 'Invalid format type'}), 400

@admin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    from app import db
    
    # Check database connection
    try:
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    # Check FAQ count
    faq_count = FAQ.query.count()
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'database': db_status,
        'faq_count': faq_count,
        'timestamp': datetime.utcnow().isoformat()
    })
