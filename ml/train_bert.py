"""
Optional script to fine-tune DistilBERT for Fake News Detection.
Requires: pip install transformers datasets torch
"""

import os
import argparse
import pandas as pd
import numpy as np

try:
    import torch
    from transformers import (
        DistilBertTokenizer, 
        DistilBertForSequenceClassification,
        Trainer, 
        TrainingArguments
    )
    from datasets import Dataset
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
except ImportError:
    print("Missing dependencies. Run: pip install transformers datasets torch scikit-learn")
    import sys
    sys.path.exit(1)


def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }


def train_bert(data_path, out_dir, sample_size=10000):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Map cols
    if 'title' in df.columns:
        df['text'] = df['title'].fillna('') + " - " + df['text'].fillna('')
        
    if df['label'].dtype == object:
        df['label'] = df['label'].astype(str).str.upper().map({'FAKE': 1, 'REAL': 0, 'TRUE': 0, 'FALSE': 1})
        
    df = df.dropna(subset=['text', 'label'])
    
    # Take a sample for reasonable training time on standard hardware
    if len(df) > sample_size:
        print(f"Sampling {sample_size} rows for BERT training...")
        df = df.sample(sample_size, random_state=42)
        
    # Split
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])
    
    # Convert to HF Datasets
    train_dataset = Dataset.from_pandas(train_df[['text', 'label']])
    test_dataset = Dataset.from_pandas(test_df[['text', 'label']])
    
    print("Loading DistilBERT tokenizer...")
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding="max_length", truncation=True, max_length=512)
        
    print("Tokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_test = test_dataset.map(tokenize_function, batched=True)
    
    print("Loading model...")
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased', 
        num_labels=2,
        id2label={0: 'REAL', 1: 'FAKE'},
        label2id={'REAL': 0, 'FAKE': 1}
    )
    
    training_args = TrainingArguments(
        output_dir=out_dir,
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_test,
        compute_metrics=compute_metrics,
    )
    
    print("Starting training...")
    trainer.train()
    
    print("Evaluating...")
    print(trainer.evaluate())
    
    print(f"Saving final model to {out_dir}/distilbert_fakenews...")
    save_path = os.path.join(out_dir, "distilbert_fakenews")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, required=True)
    parser.add_argument('--out', type=str, default='saved_models')
    parser.add_argument('--sample', type=int, default=10000, help="Number of rows to use")
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    out_dir = os.path.join(base_dir, args.out)
    
    train_bert(args.data, out_dir, args.sample)
