"""
ML classifier service.
Wraps the trained TF-IDF + Logistic Regression model for inference,
with fallback demo predictions when no model is available.
"""

import os
import json
import numpy as np

# Global model cache
_model = None
_vectorizer = None
_model_type = None


def _get_model_paths():
    """Get model file paths from config or defaults."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    model_dir = os.path.join(base_dir, 'saved_models')
    return {
        'pipeline': os.path.join(model_dir, 'tfidf_logreg_pipeline.joblib'),
        'vectorizer': os.path.join(model_dir, 'tfidf_vectorizer.joblib'),
        'model': os.path.join(model_dir, 'logreg_model.joblib'),
    }


def load_model():
    """Load the trained model into memory. Returns True if successful."""
    global _model, _vectorizer, _model_type

    if _model is not None:
        return True

    paths = _get_model_paths()

    try:
        import joblib

        # Try loading the full pipeline first
        if os.path.exists(paths['pipeline']):
            _model = joblib.load(paths['pipeline'])
            _model_type = 'pipeline'
            print(f"[Classifier] Loaded pipeline model from {paths['pipeline']}")
            return True

        # Try loading vectorizer + model separately
        if os.path.exists(paths['vectorizer']) and os.path.exists(paths['model']):
            _vectorizer = joblib.load(paths['vectorizer'])
            _model = joblib.load(paths['model'])
            _model_type = 'separate'
            print(f"[Classifier] Loaded separate vectorizer + model")
            return True

    except Exception as e:
        print(f"[Classifier] Error loading model: {e}")

    print("[Classifier] No trained model found. Using demo mode with heuristic predictions.")
    _model_type = 'demo'
    return False


def _demo_predict(text):
    """
    Heuristic-based demo prediction when no ML model is available.
    Uses simple text features to generate a plausible prediction.
    """
    from app.services.preprocessor import clean_text

    text_lower = clean_text(text)
    fake_score = 0.0

    # Sensationalist language indicators
    sensational_words = [
        'shocking', 'breaking', 'unbelievable', 'you won\'t believe',
        'exposed', 'conspiracy', 'secret', 'they don\'t want you to know',
        'mainstream media', 'wake up', 'hoax', 'scam', 'urgent',
        'bombshell', 'scandal', 'coverup', 'deep state', 'alarming',
        'terrifying', 'miracle', 'cure', 'banned', 'censored'
    ]
    for word in sensational_words:
        if word in text_lower:
            fake_score += 0.08

    # Excessive punctuation (!!!???)
    exclamation_count = text.count('!')
    question_count = text.count('?')
    if exclamation_count > 3:
        fake_score += 0.1
    if question_count > 5:
        fake_score += 0.05

    # ALL CAPS ratio
    words = text.split()
    if words:
        caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / len(words)
        if caps_ratio > 0.15:
            fake_score += 0.15

    # Very short text is suspicious
    if len(text.split()) < 20:
        fake_score += 0.1

    # Clamp score
    fake_score = min(fake_score, 0.95)
    fake_score = max(fake_score, 0.05)

    # If nothing suspicious, lean towards real
    if fake_score < 0.3:
        return {
            'label': 'REAL',
            'confidence': round(1.0 - fake_score, 4),
            'top_features': [],
            'model_used': 'demo_heuristic'
        }
    else:
        return {
            'label': 'FAKE',
            'confidence': round(fake_score, 4),
            'top_features': [w for w in sensational_words if w in text_lower][:10],
            'model_used': 'demo_heuristic'
        }


def predict(text):
    """
    Classify text as REAL or FAKE.
    
    Returns:
        dict: {
            'label': 'REAL' or 'FAKE',
            'confidence': float (0-1),
            'top_features': list of influential words,
            'model_used': str
        }
    """
    global _model, _vectorizer, _model_type

    if _model_type is None:
        load_model()

    if _model_type == 'demo' or _model is None:
        return _demo_predict(text)

    from app.services.preprocessor import preprocess_pipeline

    processed_text = preprocess_pipeline(text)

    try:
        if _model_type == 'pipeline':
            # Pipeline has vectorizer + model combined
            proba = _model.predict_proba([processed_text])[0]
            prediction = _model.predict([processed_text])[0]

            # Extract top features from the pipeline
            top_features = _extract_top_features_pipeline(processed_text)

        elif _model_type == 'separate':
            # Separate vectorizer and model
            tfidf_vector = _vectorizer.transform([processed_text])
            proba = _model.predict_proba(tfidf_vector)[0]
            prediction = _model.predict(tfidf_vector)[0]

            top_features = _extract_top_features_separate(tfidf_vector)

        else:
            return _demo_predict(text)

        # Map prediction to label
        label = 'FAKE' if prediction == 1 else 'REAL'
        confidence = float(max(proba))

        return {
            'label': label,
            'confidence': round(confidence, 4),
            'top_features': top_features,
            'model_used': 'tfidf_logreg'
        }

    except Exception as e:
        print(f"[Classifier] Prediction error: {e}")
        return _demo_predict(text)


def _extract_top_features_pipeline(text, n=10):
    """Extract top contributing features from a sklearn Pipeline."""
    try:
        vectorizer = _model.named_steps.get('tfidf') or _model.named_steps.get('vectorizer')
        classifier = _model.named_steps.get('classifier') or _model.named_steps.get('model')

        if vectorizer is None or classifier is None:
            return []

        feature_names = vectorizer.get_feature_names_out()
        tfidf_vector = vectorizer.transform([text])
        coefficients = classifier.coef_[0]

        # Get feature indices present in this text
        nonzero_indices = tfidf_vector.nonzero()[1]
        feature_scores = [
            (feature_names[i], float(coefficients[i] * tfidf_vector[0, i]))
            for i in nonzero_indices
        ]
        feature_scores.sort(key=lambda x: abs(x[1]), reverse=True)
        return [f[0] for f in feature_scores[:n]]

    except Exception:
        return []


def _extract_top_features_separate(tfidf_vector, n=10):
    """Extract top contributing features from separate vectorizer + model."""
    try:
        feature_names = _vectorizer.get_feature_names_out()
        coefficients = _model.coef_[0]

        nonzero_indices = tfidf_vector.nonzero()[1]
        feature_scores = [
            (feature_names[i], float(coefficients[i] * tfidf_vector[0, i]))
            for i in nonzero_indices
        ]
        feature_scores.sort(key=lambda x: abs(x[1]), reverse=True)
        return [f[0] for f in feature_scores[:n]]

    except Exception:
        return []


def get_model_info():
    """Return information about the currently loaded model."""
    return {
        'model_type': _model_type or 'not_loaded',
        'is_loaded': _model is not None,
        'paths': _get_model_paths()
    }
