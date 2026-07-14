import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_name='development'):
    """Application factory pattern."""
    app = Flask(__name__)

    # Load configuration
    from config import config_by_name
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Ensure instance and model directories exist
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'instance'), exist_ok=True)
    os.makedirs(app.config['MODEL_DIR'], exist_ok=True)
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.feed import feed_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(feed_bp, url_prefix='/api/feed')

    # Create database tables
    with app.app_context():
        from app.models.database import Article, Analysis, RSSFeed  # noqa: F401
        db.create_all()

    return app
