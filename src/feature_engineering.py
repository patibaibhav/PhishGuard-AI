"""
Feature Engineering for URL Phishing Detection
Extracts 33 features from a raw URL string — no API or network calls required.
"""

import re
import math
from urllib.parse import urlparse, parse_qs
from collections import Counter


# ========================
# CONSTANTS
# ========================

SUSPICIOUS_TLDS = {
    '.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.club',
    '.work', '.buzz', '.fit', '.win', '.bid', '.stream', '.gdn',
    '.racing', '.download', '.science', '.party', '.review',
    '.country', '.cricket', '.faith', '.accountant', '.date'
}

PHISHING_KEYWORDS = {
    'login', 'signin', 'sign-in', 'verify', 'verification',
    'secure', 'security', 'update', 'confirm', 'confirmation',
    'account', 'banking', 'password', 'credential', 'authenticate',
    'suspend', 'suspended', 'restrict', 'restricted', 'unusual',
    'alert', 'urgent', 'immediate', 'required', 'action',
    'expire', 'expired', 'unlock', 'locked', 'reset',
    'billing', 'payment', 'invoice', 'refund', 'claim'
}

BRAND_NAMES = {
    'paypal', 'amazon', 'google', 'apple', 'microsoft',
    'facebook', 'netflix', 'instagram', 'twitter', 'linkedin',
    'dropbox', 'yahoo', 'ebay', 'spotify', 'adobe',
    'chase', 'wellsfargo', 'bankofamerica', 'citibank',
    'whatsapp', 'telegram', 'snapchat', 'tiktok',
    'outlook', 'office365', 'onedrive', 'icloud'
}

URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
    'is.gd', 'buff.ly', 'rebrand.ly', 'shorturl.at',
    'tiny.cc', 'cutt.ly', 'rb.gy', 's.id', 'v.gd'
}

# Feature names (all 33)
FEATURE_NAMES = [
    'url_length', 'hostname_length', 'path_length',
    'num_dots', 'num_hyphens', 'num_underscores',
    'num_slashes', 'num_at_symbol', 'num_digits',
    'digit_ratio', 'num_special_chars', 'has_ip_address',
    'has_https', 'num_subdomains', 'suspicious_tld',
    'has_port', 'has_phishing_keywords', 'has_brand_name',
    'shannon_entropy', 'vowel_ratio', 'consonant_ratio',
    'longest_word_length', 'avg_word_length', 'has_redirect',
    'has_shortener', 'has_anchor', 'has_encoding',
    'query_param_count', 'query_length', 'path_token_count',
    'tld_in_path', 'repeated_chars', 'url_similarity_score'
]


# ========================
# HELPER FUNCTIONS
# ========================

def _shannon_entropy(text):
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


def _levenshtein_distance(s1, s2):
    """Calculate edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def _brand_similarity(domain):
    """Calculate min normalized edit distance to known brands."""
    domain_parts = domain.lower().replace('www.', '').split('.')
    domain_name = domain_parts[0] if domain_parts else domain.lower()

    min_dist = 1.0
    for brand in BRAND_NAMES:
        dist = _levenshtein_distance(domain_name, brand)
        normalized = dist / max(len(domain_name), len(brand), 1)
        min_dist = min(min_dist, normalized)
    return round(min_dist, 4)


def _count_repeated(text):
    """Count sequences of 3+ repeated characters."""
    count = 0
    i = 0
    while i < len(text) - 2:
        if text[i] == text[i + 1] == text[i + 2]:
            count += 1
            while i < len(text) - 1 and text[i] == text[i + 1]:
                i += 1
        i += 1
    return count


# ========================
# MAIN FEATURE EXTRACTION
# ========================

def extract_features(url):
    """
    Extract 33 features from a raw URL string.

    Parameters:
        url (str): The URL to analyze

    Returns:
        dict: Dictionary with feature names as keys and values
    """
    features = {}

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception:
        parsed = urlparse("http://error.com")

    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""
    scheme = parsed.scheme or ""
    url_lower = url.lower()

    # --- Lexical / String Features ---

    # 1. URL length
    features['url_length'] = len(url)

    # 2. Hostname length
    features['hostname_length'] = len(hostname)

    # 3. Path length
    features['path_length'] = len(path)

    # 4. Number of dots
    features['num_dots'] = url.count('.')

    # 5. Number of hyphens
    features['num_hyphens'] = url.count('-')

    # 6. Number of underscores
    features['num_underscores'] = url.count('_')

    # 7. Number of slashes
    features['num_slashes'] = url.count('/')

    # 8. Number of @ symbols (phishing indicator)
    features['num_at_symbol'] = url.count('@')

    # 9. Number of digits
    num_digits = sum(c.isdigit() for c in url)
    features['num_digits'] = num_digits

    # 10. Digit ratio
    features['digit_ratio'] = round(num_digits / max(len(url), 1), 4)

    # 11. Number of special characters
    special = sum(1 for c in url if not c.isalnum() and c not in './-_:?=&')
    features['num_special_chars'] = special

    # 12. Has IP address
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    features['has_ip_address'] = 1 if re.search(ip_pattern, hostname) else 0

    # 13. Has HTTPS
    features['has_https'] = 1 if scheme == 'https' else 0

    # 14. Number of subdomains
    subdomain_count = hostname.count('.') - 1 if hostname.count('.') > 1 else 0
    features['num_subdomains'] = max(subdomain_count, 0)

    # 15. Suspicious TLD
    has_suspicious = 0
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld) or url_lower.endswith(tld):
            has_suspicious = 1
            break
    features['suspicious_tld'] = has_suspicious

    # 16. Has non-standard port
    has_port = 0
    if parsed.port and parsed.port not in (80, 443):
        has_port = 1
    features['has_port'] = has_port

    # --- Keyword / Entropy Features ---

    # 17. Has phishing keywords
    keyword_count = sum(1 for kw in PHISHING_KEYWORDS if kw in url_lower)
    features['has_phishing_keywords'] = min(keyword_count, 10)

    # 18. Has brand name (in non-brand domain)
    brand_count = sum(1 for brand in BRAND_NAMES if brand in url_lower)
    features['has_brand_name'] = min(brand_count, 5)

    # 19. Shannon entropy
    features['shannon_entropy'] = _shannon_entropy(url)

    # 20. Vowel ratio
    letters = [c for c in url_lower if c.isalpha()]
    num_vowels = sum(1 for c in letters if c in 'aeiou')
    features['vowel_ratio'] = round(num_vowels / max(len(letters), 1), 4)

    # 21. Consonant ratio
    num_consonants = len(letters) - num_vowels
    features['consonant_ratio'] = round(num_consonants / max(len(letters), 1), 4)

    # 22. Longest word length
    words = re.split(r'[^a-zA-Z]', url)
    words = [w for w in words if w]
    features['longest_word_length'] = max((len(w) for w in words), default=0)

    # 23. Average word length
    features['avg_word_length'] = round(
        sum(len(w) for w in words) / max(len(words), 1), 4
    )

    # --- Structural Features ---

    # 24. Has redirect (// after scheme)
    after_scheme = url.split('://', 1)[-1] if '://' in url else url
    features['has_redirect'] = 1 if '//' in after_scheme else 0

    # 25. Has URL shortener
    features['has_shortener'] = 1 if any(s in url_lower for s in URL_SHORTENERS) else 0

    # 26. Has anchor (#)
    features['has_anchor'] = 1 if '#' in url else 0

    # 27. Has percent encoding
    features['has_encoding'] = 1 if '%' in url else 0

    # 28. Query parameter count
    params = parse_qs(query)
    features['query_param_count'] = len(params)

    # 29. Query string length
    features['query_length'] = len(query)

    # 30. Path token count (depth)
    path_tokens = [t for t in path.split('/') if t]
    features['path_token_count'] = len(path_tokens)

    # 31. TLD in path (suspicious)
    tld_extensions = ['.com', '.net', '.org', '.php', '.html', '.aspx', '.jsp']
    features['tld_in_path'] = 1 if any(ext in path.lower() for ext in tld_extensions) else 0

    # 32. Repeated characters
    features['repeated_chars'] = _count_repeated(url)

    # 33. URL similarity to known brands (Levenshtein)
    features['url_similarity_score'] = _brand_similarity(hostname)

    return features


def extract_feature_vector(url):
    """Extract features as a list (same order as FEATURE_NAMES)."""
    features = extract_features(url)
    return [features[name] for name in FEATURE_NAMES]


# ========================
# TEST
# ========================
if __name__ == "__main__":
    test_urls = [
        "https://www.google.com",
        "http://paypal-secure-login.tk/verify/account",
        "http://192.168.1.1/banking/login",
        "https://www.amazon.com/dp/B08N5WRWNW",
        "http://g00gle-security.com/alert/signin",
    ]

    print("Feature Extraction Test")
    print("=" * 60)

    for url in test_urls:
        features = extract_features(url)
        risk_indicators = sum([
            features['has_ip_address'],
            features['suspicious_tld'],
            features['has_phishing_keywords'] > 2,
            features['num_at_symbol'] > 0,
            features['has_shortener'],
            not features['has_https'],
        ])
        print(f"\n  URL: {url}")
        print(f"  Length: {features['url_length']}")
        print(f"  Entropy: {features['shannon_entropy']}")
        print(f"  Has IP: {features['has_ip_address']}")
        print(f"  Suspicious TLD: {features['suspicious_tld']}")
        print(f"  Phishing keywords: {features['has_phishing_keywords']}")
        print(f"  Brand similarity: {features['url_similarity_score']}")
        print(f"  Risk indicators: {risk_indicators}/6")
        print("-" * 60)
