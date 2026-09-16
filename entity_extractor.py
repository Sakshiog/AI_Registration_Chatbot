import re


INTERNSHIP_DOMAINS = [
    "data science",
    "data analytics",
    "artificial intelligence",
    "machine learning",
    "python development",
    "web development",
    "full stack development",
    "java development",
    "cloud computing",
    "cyber security",
    "android development"
]


def extract_email(text):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return None


def extract_phone(text):
    match = re.search(r"\b[6-9]\d{9}\b", text)

    if match:
        return match.group(0)

    return None


def extract_duration(text):
    pattern = r"\b\d+\s*(day|days|week|weeks|month|months)\b"

    match = re.search(
        pattern,
        text.lower()
    )

    if match:
        return match.group(0)

    return None


def extract_domain(text):
    text_lower = text.lower()

    for domain in INTERNSHIP_DOMAINS:
        if domain in text_lower:
            return domain.title()

    return None


def extract_name(text):
    patterns = [
        r"my name is ([A-Za-z]+(?:\s+[A-Za-z]+)*)",
        r"i am ([A-Za-z]+(?:\s+[A-Za-z]+)*)",
        r"i'm ([A-Za-z]+(?:\s+[A-Za-z]+)*)"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None


def extract_entities(text):
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "domain": extract_domain(text),
        "duration": extract_duration(text)
    }