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

## ⚠️ Challenges & Bugs I Faced

Building this project was far from smooth. Here are the real problems I ran into:

### 🐛 Bug 1 — Every article was classified as REAL
The heuristic classifier had a critical flaw: it passed all text through a `clean_text()` function that **lowercased everything before checking for ALL CAPS**. This meant the ALL CAPS detector was always blind. On top of that, the scoring threshold was wrong and the function returned `REAL` by default for almost anything. Every article — no matter how outrageous — came back "LIKELY REAL."

### 🐛 Bug 2 — Confidence score always showed 0%
The results detail page loaded analysis data from the database. Sentiment values were stored as `None`, and when the JavaScript tried to call `.toFixed(2)` on a `null` value, it threw a silent crash — breaking the **entire rendering function** and leaving every score at 0%.

### 🐛 Bug 3 — Sentiment scores always 0%
The sentiment lexicon was too narrow. Words like `shocking`, `exposed`, `furious`, `inflation`, `raised`, `confirmed` — extremely common in news — were missing entirely. The scorer matched zero words in most articles and returned blank scores.

### 🐛 Bug 4 — Key Indicators section was always empty
The `features` field from the classifier was never populated in heuristic mode. The frontend correctly hid the section when the array was empty — but the array was always empty because the classifier never recorded which signals it triggered.

### 🐛 Bug 5 — URL scraping failed silently
When a user submitted a URL, the scraper sometimes returned empty text (JS-heavy pages, 403 errors, timeouts) — and the app would classify that empty string as "REAL" with no error shown to the user.

---

## 🔧 How I Fixed Them

| Bug | Root Cause | Fix Applied |
|---|---|---|
| Everything classified REAL | `clean_text()` lowercasing before caps detection | Rewrote `classifier.py` with 9 FAKE signal categories using original-case text |
| Confidence always 0% | `None` DB values crashed JS renderer silently | Added null safety defaults (`0.0`) in `database.py` `to_dict()` |
| Sentiment always 0% | Lexicon missing common news vocabulary | Expanded with ~45 news-specific words (`shocking`, `exposed`, `inflation`, etc.) |
| Key Indicators empty | Classifier never logged triggered signals | Modified classifier to return `features` list of every triggered signal phrase |
| URL scraping silent failure | No text length check, no HTTP error handling | Added 50-char minimum, specific 403/404/timeout messages, JS-page detection |

---

## 🌍 Real-World Impact

Misinformation is one of the most serious challenges of our time. Studies show that:
- False news spreads **6x faster** than true news on social media *(MIT, 2018)*
- During elections and pandemics, misinformation directly influences public behavior and safety
- Most people cannot reliably distinguish real from fake news without assistance

**VeritasAI addresses this by:**

- **Making AI fact-checking accessible to everyone** — no technical knowledge needed, just paste an article
- **Being explainable** — the "Key Indicators" section shows exactly *why* an article was flagged, teaching users to spot patterns themselves
- **Covering multiple angles** — sentiment, source credibility, and linguistic patterns together are more reliable than any single signal alone
- **Working without expensive infrastructure** — the heuristic classifier works immediately, no GPU or trained model required, making it deployable in schools, newsrooms, and community platforms

> This project shows that even a lightweight open-source system can meaningfully help identify misinformation patterns — and that building it honestly, including fixing real bugs, is part of the learning.

---

## 📄 License
MIT License


