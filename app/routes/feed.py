"""
RSS feed management API routes.
"""

import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app import db
from app.models.database import RSSFeed, Article, Analysis
from app.services.rss_fetcher import fetch_feed, validate_feed_url
from app.services.classifier import predict, load_model
from app.services.sentiment import analyze_sentiment
from app.services.source_analyzer import analyze_source

feed_bp = Blueprint('feed', __name__)


@feed_bp.route('/add', methods=['POST'])
def add_feed():
    """
    Add a new RSS feed to monitor.
    
    Accepts JSON: { "url": "...", "name": "..." (optional) }
    """
    data = request.get_json()
    if not data or not data.get('url'):
        return jsonify({'error': 'Feed URL is required'}), 400

    url = data['url'].strip()
    name = data.get('name', '').strip()

    # Check if already exists
    existing = RSSFeed.query.filter_by(url=url).first()
    if existing:
        return jsonify({'error': 'This feed URL is already being monitored', 'feed': existing.to_dict()}), 409

    # Validate the feed
    validation = validate_feed_url(url)
    if not validation['valid']:
        return jsonify({'error': f"Invalid feed: {validation['error']}"}), 400

    feed = RSSFeed(
        url=url,
        name=name or validation.get('title', ''),
        is_active=True,
    )
    db.session.add(feed)
    db.session.commit()

    return jsonify({
        'message': 'Feed added successfully',
        'feed': feed.to_dict()
    }), 201


@feed_bp.route('/list', methods=['GET'])
def list_feeds():
    """List all monitored RSS feeds."""
    feeds = RSSFeed.query.order_by(RSSFeed.created_at.desc()).all()
    return jsonify({
        'feeds': [f.to_dict() for f in feeds]
    })


@feed_bp.route('/refresh', methods=['POST'])
def refresh_feeds():
    """
    Fetch new articles from all active RSS feeds and analyze them.
    """
    load_model()

    feeds = RSSFeed.query.filter_by(is_active=True).all()

    if not feeds:
        return jsonify({'message': 'No active feeds to refresh', 'articles_analyzed': 0})

    total_analyzed = 0
    results = []

    for feed_record in feeds:
        feed_data = fetch_feed(feed_record.url, max_entries=10)

        if feed_data['error']:
            results.append({
                'feed': feed_record.name or feed_record.url,
                'error': feed_data['error'],
                'articles': 0
            })
            continue

        feed_articles = 0
        for entry in feed_data['entries']:
            # Skip if we've already analyzed this URL
            if entry.get('link'):
                existing = Article.query.filter_by(source_url=entry['link']).first()
                if existing:
                    continue

            text = entry.get('summary', '')
            title = entry.get('title', '')

            if not text and not title:
                continue

            full_text = f"{title} {text}".strip()

            # Classify
            classification = predict(full_text)
            sentiment = analyze_sentiment(full_text)
            source = analyze_source(full_text)

            # Store
            article = Article(
                title=title,
                text=text,
                source_url=entry.get('link', ''),
                source_name=feed_record.name or feed_data.get('feed_title', ''),
            )
            db.session.add(article)
            db.session.flush()

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
            feed_articles += 1
            total_analyzed += 1

        # Update last_fetched
        feed_record.last_fetched = datetime.now(timezone.utc)

        results.append({
            'feed': feed_record.name or feed_record.url,
            'articles': feed_articles,
            'error': None
        })

    db.session.commit()

    return jsonify({
        'message': f'Refreshed {len(feeds)} feeds, analyzed {total_analyzed} new articles',
        'articles_analyzed': total_analyzed,
        'feed_results': results
    })


@feed_bp.route('/delete/<int:feed_id>', methods=['DELETE'])
def delete_feed(feed_id):
    """Delete a monitored RSS feed."""
    feed = RSSFeed.query.get_or_404(feed_id)
    db.session.delete(feed)
    db.session.commit()
    return jsonify({'message': 'Feed deleted successfully'})


@feed_bp.route('/toggle/<int:feed_id>', methods=['POST'])
def toggle_feed(feed_id):
    """Toggle a feed's active status."""
    feed = RSSFeed.query.get_or_404(feed_id)
    feed.is_active = not feed.is_active
    db.session.commit()
    return jsonify({
        'message': f"Feed {'activated' if feed.is_active else 'deactivated'}",
        'feed': feed.to_dict()
    })
