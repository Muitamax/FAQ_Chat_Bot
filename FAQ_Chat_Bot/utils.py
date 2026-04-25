import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def sanitize_phone_number(phone: str) -> str:
    """Sanitize and normalize phone number format"""
    # Remove all non-numeric characters
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Remove whatsapp: prefix if present
    if phone.startswith('whatsapp:'):
        phone = phone.replace('whatsapp:', '')
    
    # Ensure it starts with +
    if not phone.startswith('+'):
        # Assume US number if no country code
        if len(phone) == 10:
            phone = '+1' + phone
        else:
            phone = '+' + phone
    
    return phone

def format_response_text(text: str) -> str:
    """Format response text for WhatsApp (remove unsupported markdown)"""
    # Convert bold markdown to WhatsApp format
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    
    # Remove other markdown
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Ensure proper line breaks
    text = text.replace('\n\n', '\n')
    
    return text.strip()

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text for better searching"""
    # Simple keyword extraction
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Remove common stop words
    stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'was', 'were', 
                  'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
                  'should', 'could', 'may', 'might', 'must', 'can', 'what', 'when', 'where', 
                  'why', 'how', 'who', 'whom', 'whose', 'i', 'you', 'he', 'she', 'it', 'we', 
                  'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 
                  'their'}
    
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    return list(set(keywords))  # Remove duplicates

def calculate_similarity(text1: str, text2: str) -> float:
    """Simple similarity calculation using word overlap"""
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_time_ago(dt: datetime) -> str:
    """Get human readable time ago string"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(weeks=1):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime('%Y-%m-%d')

def validate_faq_data(data: Dict) -> Optional[str]:
    """Validate FAQ data and return error message if invalid"""
    if not data:
        return "No data provided"
    
    if 'question' not in data or not data['question'].strip():
        return "Question is required"
    
    if 'answer' not in data or not data['answer'].strip():
        return "Answer is required"
    
    if len(data['question']) > 1000:
        return "Question too long (max 1000 characters)"
    
    if len(data['answer']) > 5000:
        return "Answer too long (max 5000 characters)"
    
    return None

def paginate_query(query, page: int = 1, per_page: int = 20):
    """Paginate a database query"""
    if page < 1:
        page = 1
    
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total = query.count()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'has_next': page * per_page < total,
        'has_prev': page > 1
    }

def generate_faq_summary(faqs: List) -> Dict:
    """Generate summary statistics for FAQs"""
    categories = {}
    total_words = 0
    
    for faq in faqs:
        # Count categories
        category = faq.category or 'Uncategorized'
        categories[category] = categories.get(category, 0) + 1
        
        # Count words
        total_words += len(faq.question.split()) + len(faq.answer.split())
    
    return {
        'total_faqs': len(faqs),
        'total_categories': len(categories),
        'categories': categories,
        'avg_words_per_faq': total_words // len(faqs) if faqs else 0,
        'most_common_category': max(categories.items(), key=lambda x: x[1])[0] if categories else None
    }

def export_to_csv(data: List[Dict], filename: str) -> bool:
    """Export data to CSV file"""
    try:
        import csv
        
        if not data:
            return False
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(data)
        
        return True
    except Exception:
        return False

def import_faqs_from_csv(filename: str) -> List[Dict]:
    """Import FAQs from CSV file"""
    try:
        import csv
        
        faqs = []
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                if 'question' in row and 'answer' in row:
                    faqs.append({
                        'question': row['question'].strip(),
                        'answer': row['answer'].strip(),
                        'category': row.get('category', '').strip() or None,
                        'keywords': row.get('keywords', '').strip() or None
                    })
        
        return faqs
    except Exception:
        return []

def is_valid_webhook_request(request) -> bool:
    """Validate that request is from Twilio"""
    # This is a simplified validation
    # In production, you should validate Twilio signatures
    return request.headers.get('User-Agent', '').startswith('TwilioProxy')

def cleanup_old_sessions(days: int = 30):
    """Clean up old user sessions"""
    from models import UserSession
    from app import db
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    old_sessions = UserSession.query.filter(UserSession.last_activity < cutoff_date).all()
    
    for session in old_sessions:
        db.session.delete(session)
    
    db.session.commit()
    return len(old_sessions)
