import os
import secrets

class Config:
    """Base configuration."""
    # Generate a secure random key if none is set via environment variable.
    # This prevents session forgery when deploying without configuring SECRET_KEY.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "instance", "fakenews.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secure cookie settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ML Model paths
    MODEL_DIR = os.path.join(BASE_DIR, 'saved_models')
    TFIDF_MODEL_PATH = os.path.join(MODEL_DIR, 'tfidf_logreg_pipeline.joblib')
    TFIDF_VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')
    BERT_MODEL_PATH = os.path.join(MODEL_DIR, 'distilbert')

    # Data paths
    DATA_DIR = os.path.join(BASE_DIR, 'data')

    # RSS Feed defaults
    DEFAULT_RSS_FEEDS = [
        'http://feeds.reuters.com/reuters/topNews',
        'http://feeds.bbci.co.uk/news/rss.xml',
        'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
    ]

    # Analysis settings
    MAX_TEXT_LENGTH = 50000
    CONFIDENCE_THRESHOLD = 0.6


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
