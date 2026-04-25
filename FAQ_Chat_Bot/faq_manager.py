import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from models import FAQ

# Download NLTK data (only need to do this once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class FAQManager:
    """Manages FAQ search and matching functionality"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.faqs = []
        self.load_faqs()
    
    def load_faqs(self):
        """Load all active FAQs from database"""
        self.faqs = self.db.query(FAQ).filter_by(is_active=True).all()
        if self.faqs:
            questions = [self.preprocess_text(faq.question) for faq in self.faqs]
            self.tfidf_matrix = self.vectorizer.fit_transform(questions)
        else:
            self.tfidf_matrix = None
    
    def preprocess_text(self, text):
        """Preprocess text for better matching"""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def find_best_answer(self, user_question, threshold=0.3):
        """Find the best matching FAQ using cosine similarity"""
        if not self.faqs or self.tfidf_matrix is None:
            return None, 0.0
        
        # Preprocess user question
        processed_question = self.preprocess_text(user_question)
        
        # Transform user question
        user_vector = self.vectorizer.transform([processed_question])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(user_vector, self.tfidf_matrix)
        max_similarity = np.max(similarities)
        best_index = np.argmax(similarities)
        
        if max_similarity >= threshold:
            return self.faqs[best_index], max_similarity
        return None, max_similarity
    
    def search_by_keywords(self, user_question):
        """Search FAQs by keywords using keyword matching"""
        user_tokens = set(word.lower() for word in word_tokenize(user_question.lower()))
        user_tokens.discard('?')
        
        # Remove common stop words
        stop_words = set(stopwords.words('english'))
        user_tokens = user_tokens - stop_words
        
        best_matches = []
        for faq in self.faqs:
            score = 0
            
            # Check question tokens
            faq_question_tokens = set(word.lower() for word in word_tokenize(faq.question.lower()))
            question_overlap = len(user_tokens.intersection(faq_question_tokens))
            score += question_overlap * 2  # Give more weight to question matches
            
            # Check answer tokens
            faq_answer_tokens = set(word.lower() for word in word_tokenize(faq.answer.lower()))
            answer_overlap = len(user_tokens.intersection(faq_answer_tokens))
            score += answer_overlap
            
            # Check keywords field if available
            if faq.keywords:
                keyword_tokens = set(word.lower() for word in faq.keywords.lower().split(','))
                keyword_overlap = len(user_tokens.intersection(keyword_tokens))
                score += keyword_overlap * 3  # Give highest weight to keyword matches
            
            # Check category
            if faq.category:
                category_tokens = set(word.lower() for word in faq.category.split())
                category_overlap = len(user_tokens.intersection(category_tokens))
                score += category_overlap * 1.5
            
            if score > 0:
                best_matches.append((faq, score))
        
        # Sort by score and return best match
        if best_matches:
            best_matches.sort(key=lambda x: x[1], reverse=True)
            return best_matches[0][0]
        return None
    
    def search_by_category(self, category_name):
        """Search FAQs by category"""
        return self.db.query(FAQ).filter_by(
            category=category_name, 
            is_active=True
        ).all()
    
    def add_faq(self, question, answer, category=None, keywords=None):
        """Add a new FAQ to the database"""
        faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            keywords=keywords
        )
        self.db.add(faq)
        self.db.commit()
        self.load_faqs()  # Reload FAQs
        return faq
    
    def update_faq(self, faq_id, **kwargs):
        """Update an existing FAQ"""
        faq = self.db.query(FAQ).get(faq_id)
        if faq:
            for key, value in kwargs.items():
                if hasattr(faq, key):
                    setattr(faq, key, value)
            self.db.commit()
            self.load_faqs()  # Reload FAQs
        return faq
    
    def delete_faq(self, faq_id):
        """Delete an FAQ (soft delete by setting is_active=False)"""
        faq = self.db.query(FAQ).get(faq_id)
        if faq:
            faq.is_active = False
            self.db.commit()
            self.load_faqs()  # Reload FAQs
        return faq
    
    def get_all_categories(self):
        """Get all unique categories"""
        categories = self.db.query(FAQ.category).filter_by(is_active=True).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
    
    def get_stats(self):
        """Get FAQ statistics"""
        total_faqs = len(self.faqs)
        categories = self.get_all_categories()
        return {
            'total_faqs': total_faqs,
            'total_categories': len(categories),
            'categories': categories
        }
