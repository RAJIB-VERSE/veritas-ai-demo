"""
Train the TF-IDF + Logistic Regression model.

Usage:
    python ml/train_tfidf.py --data data/dataset.csv
"""

import os
import argparse
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Ensure import paths work
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.preprocessor import clean_text


def load_and_prepare_data(file_path):
    """Load dataset and prepare text features."""
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path)

    # Standardize column names if possible
    # We expect 'title', 'text', and 'label' (or similar)
    col_mapping = {
        'title': 'title', 'headline': 'title',
        'text': 'text', 'content': 'text',
        'label': 'label', 'target': 'label', 'class': 'label'
    }
    df.rename(columns=lambda x: col_mapping.get(x.lower(), x.lower()), inplace=True)

    if 'text' not in df.columns:
        raise ValueError("Dataset must contain a 'text' column.")
    if 'label' not in df.columns:
        raise ValueError("Dataset must contain a 'label' column.")

    # Drop missing text
    df = df.dropna(subset=['text'])

    # Merge title and text if title exists
    if 'title' in df.columns:
        df['title'] = df['title'].fillna('')
        df['combined_text'] = df['title'] + " " + df['text']
    else:
        df['combined_text'] = df['text']

    # Standardize labels: 0 for REAL, 1 for FAKE (common in WELFake and Kaggle datasets)
    # If labels are strings, map them
    if df['label'].dtype == object:
        df['label'] = df['label'].astype(str).str.upper()
        label_map = {'FAKE': 1, 'REAL': 0, 'TRUE': 0, 'FALSE': 1}
        df['label'] = df['label'].map(label_map)

    df = df.dropna(subset=['label'])
    
    print(f"Dataset shape after cleaning: {df.shape}")
    print(f"Label distribution:\n{df['label'].value_counts()}")
    
    return df


def train_model(df, save_dir):
    """Train and save the TF-IDF + LogReg pipeline."""
    print("Applying text cleaning (this may take a while)...")
    # Clean text - taking a sample if it's too large to speed up demo training
    if len(df) > 50000:
        print("Sampling 50,000 rows for faster training...")
        df = df.sample(50000, random_state=42)
        
    X = df['combined_text'].apply(clean_text)
    y = df['label'].astype(int)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

    # Build Pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_df=0.7, max_features=50000)),
        ('classifier', LogisticRegression(max_iter=1000, n_jobs=-1))
    ])

    # Basic Grid Search for Logistic Regression C parameter
    param_grid = {
        'classifier__C': [0.1, 1.0, 10.0]
    }

    print("Training model with GridSearchCV...")
    grid_search = GridSearchCV(pipeline, param_grid, cv=3, scoring='f1_macro', n_jobs=-1, verbose=1)
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    print(f"Best parameters: {grid_search.best_params_}")

    # Evaluate
    print("\nEvaluating on test set:")
    y_pred = best_model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=['REAL (0)', 'FAKE (1)']))
    
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(cm)

    # Save
    os.makedirs(save_dir, exist_ok=True)
    pipeline_path = os.path.join(save_dir, 'tfidf_logreg_pipeline.joblib')
    
    print(f"Saving model to {pipeline_path}...")
    joblib.dump(best_model, pipeline_path)
    
    # Also save vectorizer and model separately for flexibility
    vectorizer_path = os.path.join(save_dir, 'tfidf_vectorizer.joblib')
    model_path = os.path.join(save_dir, 'logreg_model.joblib')
    joblib.dump(best_model.named_steps['tfidf'], vectorizer_path)
    joblib.dump(best_model.named_steps['classifier'], model_path)
    
    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train TF-IDF Fake News Model")
    parser.add_argument('--data', type=str, required=True, help="Path to CSV dataset")
    parser.add_argument('--out', type=str, default='saved_models', help="Output directory")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"Error: Dataset {args.data} not found.")
        sys.exit(1)
        
    df = load_and_prepare_data(args.data)
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    out_dir = os.path.join(base_dir, args.out)
    
    train_model(df, out_dir)
