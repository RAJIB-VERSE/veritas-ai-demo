from datetime import datetime, timezone
from app import db


class Article(db.Model):
    """Stores ingested news articles."""
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=True)
    text = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(1000), nullable=True)
    source_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to analyses
    analyses = db.relationship('Analysis', backref='article', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'text': self.text[:500] + '...' if self.text and len(self.text) > 500 else self.text,
            'full_text': self.text,
            'source_url': self.source_url,
            'source_name': self.source_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'analyses': [a.to_dict() for a in self.analyses]
        }


class Analysis(db.Model):
    """Stores classification and analysis results."""
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)

    # Classification
    prediction = db.Column(db.String(10), nullable=False)  # 'REAL' or 'FAKE'
    confidence = db.Column(db.Float, nullable=False)
    model_used = db.Column(db.String(50), default='tfidf_logreg')

    # Sentiment
    sentiment_compound = db.Column(db.Float, nullable=True)
    sentiment_positive = db.Column(db.Float, nullable=True)
    sentiment_negative = db.Column(db.Float, nullable=True)
    sentiment_neutral = db.Column(db.Float, nullable=True)

    # Features & explainability
    top_features = db.Column(db.Text, nullable=True)       # JSON string
    suspicious_phrases = db.Column(db.Text, nullable=True)  # JSON string

    # Source analysis
    source_credibility = db.Column(db.String(20), nullable=True)  # 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'

    analyzed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'article_id': self.article_id,
            'prediction': self.prediction,
            'confidence': self.confidence or 0.0,
            'model_used': self.model_used,
            'sentiment': {
                'compound': self.sentiment_compound if self.sentiment_compound is not None else 0.0,
                'positive': self.sentiment_positive if self.sentiment_positive is not None else 0.0,
                'negative': self.sentiment_negative if self.sentiment_negative is not None else 0.0,
                'neutral': self.sentiment_neutral if self.sentiment_neutral is not None else 0.0,
            },
            'top_features': json.loads(self.top_features) if self.top_features else [],
            'suspicious_phrases': json.loads(self.suspicious_phrases) if self.suspicious_phrases else [],
            'source_credibility': self.source_credibility,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


class RSSFeed(db.Model):
    """Stores monitored RSS feed URLs."""
    __tablename__ = 'rss_feeds'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1000), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_fetched = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'name': self.name,
            'is_active': self.is_active,
            'last_fetched': self.last_fetched.isoformat() if self.last_fetched else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
