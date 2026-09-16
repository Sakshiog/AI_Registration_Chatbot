
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


# ============================================================
# NLTK RESOURCE SETUP
# ============================================================

def download_nltk_resources():

    resources = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]

    for path, resource in resources:

        try:
            nltk.data.find(path)

        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass


download_nltk_resources()


# ============================================================
# INITIALIZE NLP TOOLS
# ============================================================

try:
    STOP_WORDS = set(stopwords.words("english"))
except Exception:
    STOP_WORDS = set()


try:
    lemmatizer = WordNetLemmatizer()
except Exception:
    lemmatizer = None


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text).lower()

    # Remove URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    # Keep email characters
    text = re.sub(
        r"[^a-z0-9@._+\-\s]",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize_text(text):

    text = clean_text(text)

    if not text:
        return []

    try:
        return nltk.word_tokenize(text)

    except Exception:
        return text.split()


# ============================================================
# REMOVE STOPWORDS
# ============================================================

def remove_stopwords(tokens):

    if not tokens:
        return []

    if not STOP_WORDS:
        return tokens

    return [
        token
        for token in tokens
        if token not in STOP_WORDS
    ]


# ============================================================
# LEMMATIZATION
# ============================================================

def lemmatize_tokens(tokens):

    if not tokens:
        return []

    if lemmatizer is None:
        return tokens

    result = []

    for token in tokens:

        try:
            result.append(
                lemmatizer.lemmatize(token)
            )

        except Exception:
            result.append(token)

    return result


# ============================================================
# COMPLETE NLP PIPELINE
# ============================================================

def preprocess_text(text):

    cleaned = clean_text(text)

    tokens = tokenize_text(cleaned)

    tokens = remove_stopwords(tokens)

    tokens = lemmatize_tokens(tokens)

    return " ".join(tokens)
