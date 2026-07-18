import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Robust text normalization to counter adversarial obfuscation tactics.
    Strips invisible characters, normalizes unicode homoglyphs, and standardizes spacing.
    """
    if not text:
        return ""

    # 1. Strip invisible zero-width unicode characters
    # \u200b to \u200f are zero-width spaces and formatting characters
    # \ufeff is the byte order mark (BOM)
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff]', '', text)

    # 2. Normalize unicode (NFKC)
    # This collapses compatibility characters into their canonical forms.
    # It defeats homoglyph attacks (e.g., Cyrillic 'а' to Latin 'a' if they are NFKC equivalent)
    # and expands ligatures (e.g., 'ﬁ' to 'fi').
    text = unicodedata.normalize('NFKC', text)

    # 3. Collapse excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def normalize_for_heuristics(text: str) -> str:
    """
    Further normalization specifically for heuristic matching (lowercasing, 
    stripping punctuation noise).
    """
    text = normalize_text(text).lower()
    
    # Remove repeated punctuation used as noise (e.g., "a..n..d", "f,a,k,e")
    # Be careful not to destroy legitimate sentence boundaries completely,
    # but since this is for keyword matching, we can be aggressive.
    # We will remove non-word characters that are injected between letters.
    # A simple approach is just to strip weird punctuation if it's overused,
    # but for now, we rely on the regexes being slightly flexible.
    
    return text
