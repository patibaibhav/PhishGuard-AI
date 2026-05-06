"""
Utility functions for URL phishing detection.
Shannon entropy, Levenshtein distance, and URL parsing helpers.
"""

import math
import re
from collections import Counter


def shannon_entropy(text):
    """Calculate Shannon entropy of a string."""
    if not text:
        return 0.0
    counter = Counter(text)
    length = len(text)
    entropy = 0.0
    for count in counter.values():
        prob = count / length
        if prob > 0:
            entropy -= prob * math.log2(prob)
    return round(entropy, 4)


def levenshtein_distance(s1, s2):
    """Calculate Levenshtein (edit) distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def similarity_to_brands(domain):
    """
    Check how similar a domain is to known brand names.
    Returns the minimum normalized edit distance (0 = identical, 1 = very different).
    """
    known_brands = [
        "google", "facebook", "amazon", "apple", "microsoft",
        "paypal", "netflix", "instagram", "twitter", "linkedin",
        "dropbox", "yahoo", "ebay", "spotify", "adobe",
        "chase", "wellsfargo", "bankofamerica", "citibank",
        "whatsapp", "telegram", "snapchat", "tiktok"
    ]

    # Extract just the main domain name (remove TLD)
    domain_clean = domain.lower().split('.')[0] if '.' in domain else domain.lower()

    min_distance = float('inf')
    for brand in known_brands:
        dist = levenshtein_distance(domain_clean, brand)
        normalized = dist / max(len(domain_clean), len(brand))
        min_distance = min(min_distance, normalized)

    return round(min_distance, 4)


def count_vowels(text):
    """Count vowels in text."""
    return sum(1 for c in text.lower() if c in 'aeiou')


def count_consonants(text):
    """Count consonants in text."""
    return sum(1 for c in text.lower() if c.isalpha() and c not in 'aeiou')


def has_ip_pattern(text):
    """Check if text contains an IP address pattern."""
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    return bool(re.search(ip_pattern, text))


def count_repeated_chars(text):
    """Count sequences of 3+ repeated characters."""
    if not text:
        return 0
    count = 0
    i = 0
    while i < len(text) - 2:
        if text[i] == text[i + 1] == text[i + 2]:
            count += 1
            while i < len(text) - 1 and text[i] == text[i + 1]:
                i += 1
        i += 1
    return count
