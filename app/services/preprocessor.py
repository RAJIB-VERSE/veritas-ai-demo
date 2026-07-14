"""
Text preprocessing module for fake news detection.
Handles cleaning, tokenization, and normalization of news text.
"""

import re
import string


# Common English stop words (embedded to avoid NLTK download requirement at import time)
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
    "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
    'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
    'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
    'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd',
    'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't",
    'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn',
    "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}


def remove_urls(text):
    """Remove URLs from text."""
    return re.sub(r'https?://\S+|www\.\S+', '', text)


def remove_html_tags(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def remove_special_characters(text):
    """Remove special characters, keeping only letters, digits, and basic punctuation."""
    return re.sub(r'[^a-zA-Z0-9\s.,!?\'"-]', '', text)


def remove_extra_whitespace(text):
    """Collapse multiple whitespace characters into a single space."""
    return re.sub(r'\s+', ' ', text).strip()


def clean_text(text):
    """
    Full text cleaning pipeline.
    
    Applies: lowercase → URL removal → HTML stripping → special char removal →
    whitespace normalization.
    """
    if not text or not isinstance(text, str):
        return ''

    text = text.lower()
    text = remove_urls(text)
    text = remove_html_tags(text)
    text = remove_special_characters(text)
    text = remove_extra_whitespace(text)

    return text


def tokenize(text):
    """
    Simple word tokenization.
    Splits on whitespace and strips punctuation from token edges.
    """
    if not text:
        return []
    tokens = text.split()
    # Strip leading/trailing punctuation from each token
    tokens = [t.strip(string.punctuation) for t in tokens]
    # Remove empty tokens and very short ones
    tokens = [t for t in tokens if len(t) > 1]
    return tokens


def remove_stopwords(tokens):
    """Remove common English stop words from token list."""
    return [t for t in tokens if t.lower() not in STOP_WORDS]


def preprocess_pipeline(text):
    """
    Full preprocessing pipeline for model input.
    
    Returns cleaned text string ready for TF-IDF vectorization.
    """
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    tokens = remove_stopwords(tokens)
    return ' '.join(tokens)


def extract_raw_text(title, text):
    """
    Merge title and text fields for richer feature extraction.
    Handles None values gracefully.
    """
    parts = []
    if title and isinstance(title, str):
        parts.append(title.strip())
    if text and isinstance(text, str):
        parts.append(text.strip())
    return ' '.join(parts)
