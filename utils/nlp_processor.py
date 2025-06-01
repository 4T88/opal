import spacy
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple, Optional

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('vader_lexicon')

class NLPProcessor:
    def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load('en_core_web_sm')
        self.sia = SentimentIntensityAnalyzer()
        
        # Common task categories and their keywords
        self.category_keywords = {
            'work': ['meeting', 'report', 'presentation', 'deadline', 'project', 'email'],
            'personal': ['family', 'friend', 'home', 'house', 'personal'],
            'health': ['exercise', 'workout', 'gym', 'diet', 'health', 'fitness'],
            'learning': ['study', 'learn', 'course', 'read', 'practice', 'training'],
            'finance': ['bill', 'payment', 'budget', 'expense', 'finance', 'money'],
            'social': ['party', 'event', 'gathering', 'social', 'meet'],
            'travel': ['trip', 'travel', 'vacation', 'flight', 'hotel', 'booking']
        }
        
        # Time-related keywords
        self.time_keywords = {
            'today': 0,
            'tomorrow': 1,
            'next week': 7,
            'next month': 30,
            'in a week': 7,
            'in a month': 30
        }
    
    def process_task_input(self, text: str) -> Dict:
        """
        Process natural language task input and extract structured information
        """
        doc = self.nlp(text)
        
        # Extract basic information
        title = self._extract_title(doc)
        description = text
        
        # Extract due date
        due_date = self._extract_due_date(doc)
        
        # Extract category
        category = self._categorize_task(doc)
        
        # Extract complexity score
        complexity_score = self._calculate_complexity(doc)
        
        # Extract sentiment score
        sentiment_score = self._analyze_sentiment(doc)
        
        # Extract keywords
        keywords = self._extract_keywords(doc)
        
        # Extract estimated duration
        estimated_duration = self._extract_duration(doc)
        
        return {
            'title': title,
            'description': description,
            'due_date': due_date,
            'category': category,
            'complexity_score': complexity_score,
            'sentiment_score': sentiment_score,
            'keywords': keywords,
            'estimated_duration': estimated_duration
        }
    
    def _extract_title(self, doc) -> str:
        """Extract a concise title from the input text"""
        # Get the first sentence or first 50 characters
        first_sent = next(doc.sents).text
        return first_sent[:50].strip()
    
    def _extract_due_date(self, doc) -> Optional[datetime]:
        """Extract due date from the text"""
        text = doc.text.lower()
        
        # Check for relative time expressions
        for keyword, days in self.time_keywords.items():
            if keyword in text:
                return datetime.utcnow() + timedelta(days=days)
        
        # Check for specific date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{2,4})',  # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if '/' in pattern:
                        # Handle DD/MM/YYYY or MM/DD/YYYY
                        parts = match.groups()
                        if len(parts[2]) == 2:
                            year = 2000 + int(parts[2])
                        else:
                            year = int(parts[2])
                        return datetime(year, int(parts[1]), int(parts[0]))
                    else:
                        # Handle DD Month YYYY
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        day = int(match.group(1))
                        month = month_map[match.group(2).lower()]
                        year = int(match.group(3))
                        return datetime(year, month, day)
                except ValueError:
                    continue
        
        return None
    
    def _categorize_task(self, doc) -> str:
        """Categorize the task based on its content"""
        text = doc.text.lower()
        max_matches = 0
        best_category = 'other'
        
        for category, keywords in self.category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        return best_category
    
    def _calculate_complexity(self, doc) -> float:
        """Calculate task complexity score (0-1)"""
        # Factors that contribute to complexity:
        # 1. Number of words
        # 2. Number of sentences
        # 3. Presence of technical terms
        # 4. Number of verbs (actions required)
        
        word_count = len(doc)
        sentence_count = len(list(doc.sents))
        verb_count = len([token for token in doc if token.pos_ == 'VERB'])
        
        # Technical terms detection (simplified)
        technical_terms = len([token for token in doc if token.pos_ == 'NOUN' and len(token.text) > 8])
        
        # Calculate complexity score
        complexity = (
            (word_count / 100) * 0.3 +  # Word count factor
            (sentence_count / 5) * 0.2 +  # Sentence count factor
            (verb_count / 10) * 0.3 +  # Verb count factor
            (technical_terms / 5) * 0.2  # Technical terms factor
        )
        
        return min(max(complexity, 0), 1)  # Normalize between 0 and 1
    
    def _analyze_sentiment(self, doc) -> float:
        """Analyze the sentiment of the task description"""
        sentiment = self.sia.polarity_scores(doc.text)
        return sentiment['compound']  # Returns a score between -1 and 1
    
    def _extract_keywords(self, doc) -> List[str]:
        """Extract important keywords from the text"""
        # Get nouns and verbs as keywords
        keywords = [
            token.lemma_.lower() for token in doc
            if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop
        ]
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(keywords))
    
    def _extract_duration(self, doc) -> Optional[int]:
        """Extract estimated duration in minutes"""
        text = doc.text.lower()
        
        # Common duration patterns
        duration_patterns = [
            (r'(\d+)\s*hours?', lambda x: int(x) * 60),
            (r'(\d+)\s*mins?', lambda x: int(x)),
            (r'(\d+)\s*minutes?', lambda x: int(x)),
            (r'(\d+)\s*days?', lambda x: int(x) * 24 * 60),
            (r'(\d+)\s*weeks?', lambda x: int(x) * 7 * 24 * 60)
        ]
        
        for pattern, converter in duration_patterns:
            match = re.search(pattern, text)
            if match:
                return converter(match.group(1))
        
        return None
    
    def analyze_task_similarity(self, task1: str, task2: str) -> float:
        """Calculate similarity between two tasks (0-1)"""
        doc1 = self.nlp(task1)
        doc2 = self.nlp(task2)
        
        # Calculate similarity using spaCy's built-in similarity
        return doc1.similarity(doc2)
    
    def suggest_task_improvements(self, text: str) -> List[str]:
        """Suggest improvements for task description"""
        suggestions = []
        doc = self.nlp(text)
        
        # Check for clarity
        if len(list(doc.sents)) > 3:
            suggestions.append("Consider breaking down the task into smaller, more manageable subtasks")
        
        # Check for specificity
        if not any(token.pos_ == 'VERB' for token in doc):
            suggestions.append("Add specific actions to make the task more actionable")
        
        # Check for time frame
        if not self._extract_due_date(doc):
            suggestions.append("Add a specific deadline or time frame")
        
        # Check for priority indicators
        if not any(word in text.lower() for word in ['urgent', 'important', 'priority', 'critical']):
            suggestions.append("Consider adding priority level or importance indicator")
        
        return suggestions 