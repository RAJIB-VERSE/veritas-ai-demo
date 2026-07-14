"""
Sentiment analysis service using a lexicon-based approach (VADER-inspired).
Provides compound, positive, negative, and neutral sentiment scores
without requiring external model downloads.
"""

import re
import math

# VADER-inspired sentiment lexicon (curated subset of high-signal words)
_POSITIVE_WORDS = {
    'good': 1.9, 'great': 3.1, 'excellent': 3.2, 'amazing': 3.1, 'wonderful': 2.8,
    'fantastic': 3.0, 'terrific': 2.8, 'outstanding': 3.1, 'brilliant': 2.9,
    'love': 2.5, 'happy': 2.7, 'joy': 2.6, 'beautiful': 2.5, 'best': 2.6,
    'perfect': 2.8, 'impressive': 2.5, 'success': 2.2, 'successful': 2.3,
    'positive': 1.8, 'agree': 1.5, 'support': 1.6, 'help': 1.4, 'helpful': 2.0,
    'improve': 1.7, 'improvement': 1.8, 'benefit': 1.9, 'progress': 1.7,
    'hope': 1.8, 'hopeful': 2.0, 'promising': 2.1, 'encourage': 1.9,
    'safe': 1.5, 'healthy': 1.8, 'peace': 2.0, 'peaceful': 2.1,
    'win': 2.0, 'victory': 2.3, 'celebrate': 2.2, 'proud': 2.1,
    'innovative': 2.0, 'breakthrough': 2.5, 'remarkable': 2.4, 'incredible': 2.6,
    'delighted': 2.5, 'pleased': 2.0, 'glad': 1.8, 'fortunate': 1.9,
    'thrive': 2.0, 'prosper': 2.1, 'achieve': 1.8, 'achievement': 2.2,
}

_NEGATIVE_WORDS = {
    'bad': -2.5, 'terrible': -3.0, 'horrible': -3.1, 'awful': -2.8,
    'worst': -3.2, 'hate': -2.7, 'angry': -2.3, 'anger': -2.1,
    'sad': -2.0, 'unhappy': -2.1, 'disaster': -2.8, 'crisis': -2.0,
    'fail': -2.3, 'failure': -2.5, 'wrong': -1.8, 'problem': -1.5,
    'danger': -2.2, 'dangerous': -2.5, 'threat': -2.1, 'threaten': -2.2,
    'attack': -2.5, 'violent': -2.8, 'violence': -2.7, 'kill': -3.0,
    'killed': -3.1, 'death': -2.5, 'dead': -2.5, 'die': -2.5,
    'fear': -2.0, 'afraid': -2.1, 'scared': -2.0, 'terror': -3.0,
    'terrorist': -3.2, 'bomb': -2.8, 'war': -2.5, 'conflict': -1.8,
    'corrupt': -2.5, 'corruption': -2.6, 'fraud': -2.7, 'lie': -2.5,
    'lies': -2.6, 'fake': -2.5, 'false': -2.0, 'misleading': -2.3,
    'scandal': -2.5, 'controversy': -1.5, 'controversial': -1.3,
    'suffer': -2.3, 'suffering': -2.5, 'pain': -2.0, 'painful': -2.2,
    'destroy': -2.8, 'destruction': -2.9, 'damage': -2.0, 'harm': -2.2,
    'crash': -2.3, 'collapse': -2.5, 'decline': -1.5, 'recession': -2.0,
    'poverty': -2.0, 'unemployment': -1.8, 'inequality': -1.5,
    'guilty': -2.5, 'crime': -2.3, 'criminal': -2.5, 'arrest': -1.8,
    'prison': -2.0, 'punishment': -1.8,
}

# Booster words that intensify sentiment
_BOOSTERS = {
    'very': 0.293, 'really': 0.293, 'extremely': 0.293, 'absolutely': 0.293,
    'incredibly': 0.293, 'remarkably': 0.293, 'especially': 0.293,
    'most': 0.293, 'totally': 0.293, 'utterly': 0.293, 'quite': 0.15,
    'rather': 0.15, 'somewhat': -0.15, 'slightly': -0.15, 'barely': -0.293,
}

# Negation words that flip sentiment
_NEGATIONS = {
    'not', "n't", 'no', 'never', 'neither', 'nor', 'nobody', 'nothing',
    'nowhere', 'hardly', 'scarcely', 'rarely', "doesn't", "don't",
    "didn't", "isn't", "wasn't", "weren't", "won't", "wouldn't",
    "couldn't", "shouldn't", "can't", "cannot",
}


def analyze_sentiment(text):
    """
    Analyze the sentiment of the given text.
    
    Returns:
        dict: {
            'compound': float (-1 to 1),
            'positive': float (0 to 1),
            'negative': float (0 to 1),
            'neutral': float (0 to 1),
            'label': str ('positive', 'negative', 'neutral'),
            'sensationalism_score': float (0 to 1)
        }
    """
    if not text or not isinstance(text, str):
        return {
            'compound': 0.0, 'positive': 0.0, 'negative': 0.0,
            'neutral': 1.0, 'label': 'neutral', 'sensationalism_score': 0.0
        }

    words = re.findall(r'\b[a-zA-Z\']+\b', text.lower())

    pos_score = 0.0
    neg_score = 0.0
    word_count = 0

    for i, word in enumerate(words):
        score = 0.0

        if word in _POSITIVE_WORDS:
            score = _POSITIVE_WORDS[word]
        elif word in _NEGATIVE_WORDS:
            score = _NEGATIVE_WORDS[word]
        else:
            continue

        # Check for preceding booster
        if i > 0 and words[i - 1] in _BOOSTERS:
            booster = _BOOSTERS[words[i - 1]]
            if score > 0:
                score += booster
            else:
                score -= booster

        # Check for preceding negation (within 3 words)
        negated = False
        for j in range(max(0, i - 3), i):
            if words[j] in _NEGATIONS or (words[j].endswith("n't")):
                negated = True
                break

        if negated:
            score *= -0.74  # Dampen negated sentiment

        if score > 0:
            pos_score += score
        else:
            neg_score += abs(score)

        word_count += 1

    # Normalize scores
    total_words = max(len(words), 1)

    # Compute compound score (normalized to -1 to 1)
    raw_compound = pos_score - neg_score
    compound = raw_compound / math.sqrt(raw_compound ** 2 + 15)  # VADER-style normalization

    # Compute proportions
    total_sentiment = pos_score + neg_score
    if total_sentiment > 0:
        pos_prop = pos_score / total_sentiment
        neg_prop = neg_score / total_sentiment
    else:
        pos_prop = 0.0
        neg_prop = 0.0

    neutral_prop = max(0.0, 1.0 - (word_count / total_words))

    # Normalize to sum to 1
    total = pos_prop + neg_prop + neutral_prop
    if total > 0:
        pos_prop /= total
        neg_prop /= total
        neutral_prop /= total

    # Label
    if compound >= 0.05:
        label = 'positive'
    elif compound <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'

    # Sensationalism score
    sensationalism = _compute_sensationalism(text)

    return {
        'compound': round(compound, 4),
        'positive': round(pos_prop, 4),
        'negative': round(neg_prop, 4),
        'neutral': round(neutral_prop, 4),
        'label': label,
        'sensationalism_score': round(sensationalism, 4)
    }


def _compute_sensationalism(text):
    """
    Compute a sensationalism score based on language patterns.
    Higher scores indicate more sensationalist language.
    """
    score = 0.0
    text_lower = text.lower()

    # Sensationalist phrases
    sensational_phrases = [
        'you won\'t believe', 'shocking', 'breaking', 'urgent',
        'exclusive', 'bombshell', 'exposed', 'revealed', 'scandal',
        'they don\'t want you to know', 'wake up', 'mainstream media',
        'cover up', 'coverup', 'conspiracy', 'deep state',
        'miracle cure', 'doctors hate', 'one weird trick',
        'this changes everything', 'what they\'re hiding',
    ]
    for phrase in sensational_phrases:
        if phrase in text_lower:
            score += 0.12

    # Excessive exclamation marks
    excl_count = text.count('!')
    if excl_count > 2:
        score += min(excl_count * 0.03, 0.2)

    # ALL CAPS words
    words = text.split()
    if words:
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        caps_ratio = caps_words / len(words)
        score += min(caps_ratio * 2, 0.3)

    # Excessive question marks
    q_count = text.count('?')
    if q_count > 3:
        score += min(q_count * 0.02, 0.1)

    return min(score, 1.0)
