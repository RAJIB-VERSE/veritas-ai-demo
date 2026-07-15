# VeritasAI: Fake News Detection and Analysis System

<video src="https://github.com/RAJIB-VERSE/veritas-ai-demo/raw/main/assets/demo.mp4" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

VeritasAI is a comprehensive, full-stack application designed to combat misinformation. It uses Machine Learning (TF-IDF + Logistic Regression, or DistilBERT) to classify news articles as "REAL" or "FAKE," along with detailed sentiment analysis and source credibility checks.

## Features

- **Text & URL Analysis:** Paste raw text or provide an article URL for automatic parsing.
- **ML Classification:** Real/Fake probability with extracted feature highlights (explainable AI).
- **Sentiment & Sensationalism:** Analyzes tone (VADER-inspired) and flags clickbait language.
- **Source Checking:** Extracts domains and checks against curated lists of credible and questionable sources.
- **RSS Feed Monitor:** Automatically fetches and analyzes news from monitored feeds.
- **Analytics Dashboard:** Visualize trends, source distributions, and historical data with Chart.js.
- **Premium UI:** Dark-mode, glassmorphism design system.

## Project Structure

```
Fake News Detection and Analysis System/
├── app/                  # Flask web application
│   ├── models/           # SQLite database models
│   ├── routes/           # API and page routes
│   ├── services/         # ML inference, NLP, and web scraping
│   ├── static/           # CSS (glassmorphism) and JS
│   └── templates/        # HTML templates
├── ml/                   # Model training scripts (TF-IDF & BERT)
├── data/                 # Datasets (e.g., WELFake)
├── saved_models/         # Serialized pipelines (.joblib)
├── config.py             # Configuration
├── run.py                # Entry point
└── requirements.txt      # Dependencies
```

## Quick Start (Demo Mode)

You can run the app immediately without training a model. It will use a heuristic-based "Demo Mode" for classification until a model is trained.

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the Flask app:**
   ```bash
   python run.py
   ```
3. **Open in browser:** `http://localhost:5000`

## Training a Custom Model (TF-IDF + LogReg)

For real ML classification, you'll need a dataset like [WELFake from Kaggle](https://www.kaggle.com/datasets/saurabhshahane/fake-news-classification).

1. Download the dataset and place it in the `data/` folder (e.g., `data/WELFake_Dataset.csv`).
2. Run the training script:
   ```bash
   python ml/train_tfidf.py --data data/WELFake_Dataset.csv
   ```
3. The pipeline will be saved to `saved_models/tfidf_logreg_pipeline.joblib`. The web app will automatically load it on the next restart.

## Advanced: DistilBERT Fine-Tuning

If you want state-of-the-art performance using deep learning:

1. Install extra dependencies: `pip install transformers datasets torch`
2. Run the BERT training script:
   ```bash
   python ml/train_bert.py --data data/WELFake_Dataset.csv
   ```
3. Push to Hugging Face Hub (optional):
   ```bash
   python ml/export_hf.py --repo_id "your_username/fakenews-model" --token "YOUR_HF_TOKEN"
   ```

## License
MIT License
