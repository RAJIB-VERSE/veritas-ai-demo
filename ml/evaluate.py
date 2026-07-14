"""
Evaluate a trained model on a test dataset.

Usage:
    python ml/evaluate.py --data data/test.csv --model saved_models/tfidf_logreg_pipeline.joblib
"""

import os
import argparse
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.preprocessor import clean_text


def evaluate(data_path, model_path):
    print(f"Loading model from {model_path}...")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
        
    model = joblib.load(model_path)
    
    print(f"Loading test data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Minimal prep mapping
    if 'title' in df.columns and 'text' in df.columns:
        df['combined_text'] = df['title'].fillna('') + " " + df['text'].fillna('')
    elif 'text' in df.columns:
        df['combined_text'] = df['text'].fillna('')
    else:
        raise ValueError("Dataset must contain a 'text' column.")
        
    if df['label'].dtype == object:
        df['label'] = df['label'].astype(str).str.upper().map({'FAKE': 1, 'REAL': 0, 'TRUE': 0, 'FALSE': 1})
        
    df = df.dropna(subset=['combined_text', 'label'])
    
    print("Preprocessing text...")
    X = df['combined_text'].apply(clean_text)
    y_true = df['label'].astype(int)
    
    print("Running inference...")
    y_pred = model.predict(X)
    
    print("\n--- Evaluation Results ---")
    print(classification_report(y_true, y_pred, target_names=['REAL (0)', 'FAKE (1)']))
    
    if hasattr(model, 'predict_proba'):
        y_prob = model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y_true, y_prob)
        print(f"ROC-AUC Score: {auc:.4f}")
        
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate Fake News Model")
    parser.add_argument('--data', type=str, required=True, help="Path to test CSV dataset")
    parser.add_argument('--model', type=str, required=True, help="Path to joblib pipeline model")
    args = parser.parse_args()
    
    evaluate(args.data, args.model)
