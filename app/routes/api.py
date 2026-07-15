"""
REST API routes for article analysis, history, and statistics.
"""

import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app import db
from app.models.database import Article, Analysis
from app.services.classifier import predict, load_model
from app.services.sentiment import analyze_sentiment
from app.services.source_analyzer import analyze_source
from app.services.preprocessor import clean_text

api_bp = Blueprint('api', __name__)


@api_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze a news article for fake news indicators.
    
    Accepts JSON:
        { "text": "...", "title": "..." (optional), "url": "..." (optional) }
    
    Returns full analysis including classification, sentiment, and source analysis.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    text = data.get('text', '').strip()
    title = data.get('title', '').strip()
    url = data.get('url', '').strip()

    # If URL provided but no text, try to fetch the article
    if url and not text:
        from app.services.rss_fetcher import fetch_article_content
        fetched = fetch_article_content(url)
        if fetched['error']:
            return jsonify({'error': f"Could not fetch article: {fetched['error']}"}), 400
        text = fetched['text']
        if not title:
            title = fetched['title']

    if not text or len(text.strip()) < 50:
        return jsonify({
            'error': 'Not enough text to analyze. Please provide at least 50 characters of article text, or paste the article text directly.'
        }), 400

    if len(text) > 50000:
        return jsonify({'error': 'Text exceeds maximum length of 50,000 characters'}), 400

    # Ensure model is loaded
    load_model()

    # Run classification
    classification = predict(text)

    # Run sentiment analysis
    sentiment = analyze_sentiment(text)

    # Run source analysis
    source = analyze_source(text)

    # Store in database
    article = Article(
        title=title or None,
        text=text,
        source_url=url or None,
        source_name=source.get('domains', [None])[0] if source.get('domains') else None,
    )
    db.session.add(article)
    db.session.flush()  # Get the article ID

    analysis = Analysis(
        article_id=article.id,
        prediction=classification['label'],
        confidence=classification['confidence'],
        model_used=classification['model_used'],
        sentiment_compound=sentiment['compound'],
        sentiment_positive=sentiment['positive'],
        sentiment_negative=sentiment['negative'],
        sentiment_neutral=sentiment['neutral'],
        top_features=json.dumps(classification.get('top_features', [])),
        suspicious_phrases=json.dumps(source.get('clickbait_phrases', [])),
        source_credibility=source.get('credibility', 'UNKNOWN'),
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        'article_id': article.id,
        'analysis_id': analysis.id,
        'classification': classification,
        'sentiment': sentiment,
        'source_analysis': source,
        'created_at': article.created_at.isoformat() if article.created_at else None,
    })


@api_bp.route('/history', methods=['GET'])
def history():
    """
    Get paginated analysis history.
    
    Query params: page (default 1), per_page (default 20)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Cap at 100

    query = Article.query.order_by(Article.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'articles': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    })


@api_bp.route('/article/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Get a specific article and its analysis."""
    article = Article.query.get_or_404(article_id)
    return jsonify(article.to_dict())


@api_bp.route('/stats', methods=['GET'])
def stats():
    """
    Get aggregated statistics for the dashboard.
    Returns counts, distributions, and trend data.
    """
    total = Analysis.query.count()
    fake_count = Analysis.query.filter_by(prediction='FAKE').count()
    real_count = Analysis.query.filter_by(prediction='REAL').count()

    # Average confidence
    from sqlalchemy import func

    avg_confidence = db.session.query(func.avg(Analysis.confidence)).scalar() or 0

    # Sentiment distribution
    avg_sentiment = db.session.query(func.avg(Analysis.sentiment_compound)).scalar() or 0

    # Recent analyses (last 30)
    recent = Analysis.query.order_by(Analysis.analyzed_at.desc()).limit(30).all()

    # Daily counts for trend chart (last 30 days)
    daily_data = []
    if recent:
        from collections import defaultdict
        daily_counts = defaultdict(lambda: {'fake': 0, 'real': 0})
        for a in recent:
            if a.analyzed_at:
                day = a.analyzed_at.strftime('%Y-%m-%d')
                if a.prediction == 'FAKE':
                    daily_counts[day]['fake'] += 1
                else:
                    daily_counts[day]['real'] += 1

        for day in sorted(daily_counts.keys()):
            daily_data.append({
                'date': day,
                'fake': daily_counts[day]['fake'],
                'real': daily_counts[day]['real'],
            })

    # Source credibility distribution
    credibility_dist = {}
    for cred in ['HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
        count = Analysis.query.filter_by(source_credibility=cred).count()
        credibility_dist[cred] = count

    # Model usage
    model_dist = {}
    model_results = db.session.query(
        Analysis.model_used, func.count(Analysis.id)
    ).group_by(Analysis.model_used).all()
    for model_name, count in model_results:
        model_dist[model_name or 'unknown'] = count

    return jsonify({
        'total_analyzed': total,
        'fake_count': fake_count,
        'real_count': real_count,
        'fake_percentage': round((fake_count / total * 100) if total > 0 else 0, 1),
        'real_percentage': round((real_count / total * 100) if total > 0 else 0, 1),
        'avg_confidence': round(float(avg_confidence), 4),
        'avg_sentiment': round(float(avg_sentiment), 4),
        'daily_trend': daily_data,
        'credibility_distribution': credibility_dist,
        'model_distribution': model_dist,
    })
