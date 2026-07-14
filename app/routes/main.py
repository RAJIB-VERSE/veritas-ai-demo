"""
Main page routes — serves HTML pages.
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page with the analysis form."""
    return render_template('index.html')


@main_bp.route('/dashboard')
def dashboard():
    """Analytics dashboard with charts and statistics."""
    return render_template('dashboard.html')


@main_bp.route('/results/<int:article_id>')
def results(article_id):
    """Detailed results page for a specific article analysis."""
    return render_template('results.html', article_id=article_id)


@main_bp.route('/feed')
def feed():
    """RSS feed monitor page."""
    return render_template('feed.html')
