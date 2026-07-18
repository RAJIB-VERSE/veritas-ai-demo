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


@api_bp.route('/evaluate', methods=['POST'])
def analyze():
    """
    Analyze a news article for fake news indicators.
    
    Accepts JSON:
        { "text": "...", "title": "..." (optional), "url": "..." (optional) }
    
    Returns full analysis including classification, sentiment, source analysis,
    AI-generated content detection, and live web fact-checking.

    Priority order for final verdict:
        1. AI-generated content detected → FAKE (highest priority)
        2. Fact check debunked → FAKE
        3. Fact check verified → REAL (overrides isolated headline penalty)
        4. Unverified + no attribution → FAKE penalty (only if NOT verified)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    # Input sanitization: strip HTML tags to prevent XSS
    import re as _re
    def _strip_html(s):
        return _re.sub(r'<[^>]+>', '', s) if s else ''

    text = _strip_html(data.get('text', '')).strip()
    title = _strip_html(data.get('title', '')).strip()[:500]  # Cap title length
    url = data.get('url', '').strip()

    # Validate URL format if provided
    if url and not url.startswith(('http://', 'https://')):
        url = ''  # Silently discard invalid URLs

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

    # Run source analysis (include provided URL so it can be evaluated)
    text_for_source = text
    if url:
        text_for_source += f"\n{url}"
    source = analyze_source(text_for_source)

    # ---------------------------------------------------------
    # Step 1: AI-Generated Content Detection (HIGHEST PRIORITY)
    # ---------------------------------------------------------
    from app.services.ai_detector import detect_ai_content
    try:
        ai_detection = detect_ai_content(text, verify_entities=True)
    except Exception as e:
        print(f"[AI Detection Error] {e}")
        ai_detection = {
            'is_ai_generated': False,
            'ai_probability': 0.0,
            'signals': [],
            'fictional_entities': [],
            'verified_entities': [],
        }

    # ---------------------------------------------------------
    # Step 2: Live Web Fact Checking
    # ---------------------------------------------------------
    from app.services.fact_checker import search_and_verify
    try:
        fact_check = search_and_verify(text)
    except Exception as e:
        print(f"[Fact Check Error] {e}")
        fact_check = {'status': 'error', 'message': f'Web search unavailable: {str(e)}'}

    # ---------------------------------------------------------
    # Step 3: Compute auxiliary signals
    # ---------------------------------------------------------
    from app.services.classifier import ATTRIBUTION_PHRASES
    text_lower = text.lower()
    has_attribution = any(p in text_lower for p in ATTRIBUTION_PHRASES)

    is_unknown = source.get('credibility', 'UNKNOWN') in ['UNKNOWN', 'LOW']
    is_short = source.get('suspicious_patterns', {}).get('very_short', False)
    no_urls_cited = len(source.get('urls_found', [])) == 0

    is_isolated_headline = is_short and no_urls_cited and not has_attribution
    is_unverified_article = is_unknown and no_urls_cited and not has_attribution

    # ---------------------------------------------------------
    # Step 4: Apply verdict with correct priority ordering
    # ---------------------------------------------------------
    # Track whether verdict was set by a high-priority signal
    verdict_locked = False

    # PRIORITY 1: AI-generated content detected → FAKE
    if ai_detection.get('is_ai_generated', False):
        classification['label'] = 'FAKE'
        ai_prob = ai_detection.get('ai_probability', 0.85)
        classification['fake_prob'] = max(0.90, ai_prob)
        classification['real_prob'] = 1.0 - classification['fake_prob']
        classification['confidence'] = classification['fake_prob']
        verdict_locked = True

        msg = "⚠️ AI-Generated Content: Text exhibits multiple AI authorship signals"
        if ai_detection.get('fictional_entities'):
            entities_str = ', '.join(ai_detection['fictional_entities'][:3])
            msg += f" (unverifiable entities: {entities_str})"

        if 'features' in classification:
            classification['features'].append(msg)
        if 'top_features' in classification:
            classification['top_features'].append(msg)

        # Add individual signal descriptions
        for signal_name, signal_score, signal_desc in ai_detection.get('signals', []):
            if signal_score >= 0.3:
                if 'features' in classification:
                    classification['features'].append(f"AI Signal: {signal_desc}")
                if 'top_features' in classification:
                    classification['top_features'].append(f"AI Signal: {signal_desc}")

    # PRIORITY 2: Fact check debunked → FAKE (also catches fictional qualifier)
    if not verdict_locked and fact_check.get('status') == 'debunked':
        classification['label'] = 'FAKE'
        classification['fake_prob'] = 0.95
        classification['real_prob'] = 0.05
        classification['confidence'] = 0.95
        verdict_locked = True

        if fact_check.get('ai_fabrication_detected'):
            msg = "Fact Checked: Content references fictional entities — likely AI-fabricated."
        else:
            msg = "Fact Checked: Live web search found credible sources debunking this claim."
        if 'features' in classification: classification['features'].append(msg)
        if 'top_features' in classification: classification['top_features'].append(msg)

    # PRIORITY 3: Fact check verified → REAL
    # This OVERRIDES isolated headline penalty! A verified fact is REAL
    # regardless of text length or attribution style.
    if not verdict_locked and fact_check.get('status') == 'verified':
        classifier_says_fake = classification['label'] == 'FAKE'
        classifier_high_confidence = classification.get('fake_prob', 0) >= 0.85

        if classifier_says_fake and classifier_high_confidence:
            # Conflicting signals: classifier says FAKE with high confidence
            # but web search found confirming articles. Don't flip, but note it.
            msg = "Conflicting Signal: Web search found related sources, but classifier detected strong fake indicators. Maintaining FAKE classification."
            if 'features' in classification: classification['features'].append(msg)
            if 'top_features' in classification: classification['top_features'].append(msg)
        else:
            # Web search confirmed the claim — mark as REAL
            # This intentionally overrides the isolated headline penalty
            classification['label'] = 'REAL'
            classification['real_prob'] = 0.85
            classification['fake_prob'] = 0.15
            classification['confidence'] = 0.85
            msg = "✅ Fact Checked: Live web search found credible sources verifying this claim."
            if 'features' in classification: classification['features'].append(msg)
            if 'top_features' in classification: classification['top_features'].append(msg)

        verdict_locked = True  # Don't let penalty override

    # PRIORITY 3.5: Unverified claims from unknown sources → FAKE
    # If the AI text was "humanized" to bypass the AI detector, the ML classifier might be tricked.
    # However, if it's completely fabricated, the fact checker will return 'unverified'.
    # If an unverified claim comes from an unknown source (e.g., pasted text or shady URL),
    # we apply a strong FAKE penalty because we cannot trust the ML classifier.
    if not verdict_locked and fact_check.get('status') == 'unverified':
        if is_unknown:
            classification['label'] = 'FAKE'
            classification['fake_prob'] = max(0.85, classification.get('fake_prob', 0.5) + 0.35)
            classification['real_prob'] = 1.0 - classification['fake_prob']
            classification['confidence'] = classification['fake_prob']

            msg = "⚠️ Unverified Origin: Claim cannot be verified and comes from an unknown/untrusted source."
            if 'features' in classification: classification['features'].append(msg)
            if 'top_features' in classification: classification['top_features'].append(msg)
            
            # Lock the verdict so Priority 4 doesn't override it with a weaker penalty
            verdict_locked = True

    # PRIORITY 4: Unverified + no attribution → minor penalty (ONLY if not already locked)
    if not verdict_locked:
        if is_isolated_headline or is_unverified_article:
            classification['label'] = 'FAKE'
            classification['fake_prob'] = max(0.80, classification.get('fake_prob', 0.5) + 0.3)
            classification['real_prob'] = 1.0 - classification['fake_prob']
            classification['confidence'] = classification['fake_prob']

            msg = "Unverified Claim: Lacks sources, citations, or verifiable attribution"
            if is_isolated_headline:
                msg = "Isolated Headline: No article or source provided to verify the claim"

            if 'features' in classification and isinstance(classification['features'], list):
                if msg not in classification['features']:
                    classification['features'].append(msg)
            if 'top_features' in classification and isinstance(classification['top_features'], list):
                if msg not in classification['top_features']:
                    classification['top_features'].append(msg)

    # ---------------------------------------------------------
    # Store in database
    # ---------------------------------------------------------
    article = Article(
        title=title or None,
        text=text,
        source_url=url or None,
        source_name=source.get('domains', [None])[0] if source.get('domains') else None,
    )
    db.session.add(article)
    db.session.flush()  # Get the article ID

    # Serialize AI detection for storage (only the key fields)
    ai_detection_serializable = {
        'is_ai_generated': ai_detection.get('is_ai_generated', False),
        'ai_probability': ai_detection.get('ai_probability', 0.0),
        'signals': [(n, s, d) for n, s, d in ai_detection.get('signals', [])],
        'fictional_entities': ai_detection.get('fictional_entities', []),
        'verified_entities': ai_detection.get('verified_entities', []),
    }

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
        fact_check_result=json.dumps(fact_check) if fact_check else None,
        ai_detection_result=json.dumps(ai_detection_serializable),
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        'article_id': article.id,
        'analysis_id': analysis.id,
        'classification': classification,
        'sentiment': sentiment,
        'source_analysis': source,
        'fact_check': fact_check,
        'ai_detection': ai_detection_serializable,
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
