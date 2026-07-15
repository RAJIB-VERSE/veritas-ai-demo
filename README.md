# VeritasAI — Fake News Detection & Analysis System

![VeritasAI Demo](assets/demo.gif)

> **AI-powered fake news detector** — paste any article and get an instant verdict with sentiment analysis, key indicators, source credibility, and clickbait detection.

🌐 **Live Demo:** [rajibverse.pythonanywhere.com](https://rajibverse.pythonanywhere.com/)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Real/Fake Classification** | Heuristic + TF-IDF ML classifier with explainable Key Indicators |
| 💭 **Sentiment Analysis** | Positive / Negative / Neutral scoring with sensationalism detection |
| 🔗 **Source Credibility** | Checks domains against curated credible & questionable source lists |
| 🚨 **Clickbait Detection** | Flags conspiracy language, health misinfo, and political extremism |
| 📰 **URL Scraping** | Paste a URL and let the app extract and analyze the article |
| 📡 **RSS Feed Monitor** | Auto-fetch and analyze live news from monitored feeds |
| 📊 **Analytics Dashboard** | Historical trends and source distribution charts |
| 🎨 **Premium Dark UI** | Glassmorphism design with smooth micro-animations |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python run.py

# 3. Open in browser
# http://localhost:5000
```

No model training required — the app works immediately using the built-in heuristic classifier.

---

## 🧪 Test It Yourself

**Fake news (expect FAKE):**
> SHOCKING: Deep State EXPOSED!!! Scientists Finally Admit Vaccines Cause Autism — Big Pharma FURIOUS as Mainstream Media Tries to SUPPRESS This Story!!!

**Real news (expect REAL):**
> The Federal Reserve raised interest rates by 0.25 percentage points on Wednesday, according to a statement from the central bank. Fed Chair Jerome Powell said the decision was aimed at curbing inflation, which stood at 3.2% in June.

---

## 🗂️ Project Structure

```
├── app/
│   ├── models/        # SQLite database models
│   ├── routes/        # API and page routes (api.py, main.py, feed.py)
│   ├── services/      # classifier.py, sentiment.py, rss_fetcher.py, source_analyzer.py
│   ├── static/        # CSS (glassmorphism) and JS
│   └── templates/     # HTML templates (index, results, dashboard, feed)
├── ml/                # Model training scripts (TF-IDF & BERT)
├── saved_models/      # Drop trained .joblib pipeline here
├── assets/            # Demo GIF and media
├── config.py
├── run.py
└── requirements.txt
```

---

## 🤖 Training a Custom ML Model

For higher accuracy, train on the [WELFake dataset (Kaggle)](https://www.kaggle.com/datasets/saurabhshahane/fake-news-classification):

```bash
# Download and place dataset
# data/WELFake_Dataset.csv

# Train TF-IDF + Logistic Regression pipeline
python ml/train_tfidf.py --data data/WELFake_Dataset.csv

# The pipeline is saved to saved_models/tfidf_logreg_pipeline.joblib
# Restart the app and it loads automatically
```

---

## 📄 License
MIT License
