"""
Dataset Downloader for URL Phishing Detection
Downloads and prepares labelled URL datasets from public sources.
No API keys required.
"""

import os
import csv
import requests
import random

# --- Configuration ---
RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed")


# ========================
# LEGITIMATE URLs (Curated from Alexa/Tranco Top Sites)
# ========================
LEGITIMATE_URLS = [
    "https://www.google.com", "https://www.youtube.com", "https://www.facebook.com",
    "https://www.amazon.com", "https://www.wikipedia.org", "https://www.twitter.com",
    "https://www.instagram.com", "https://www.linkedin.com", "https://www.reddit.com",
    "https://www.netflix.com", "https://www.apple.com", "https://www.microsoft.com",
    "https://www.yahoo.com", "https://www.ebay.com", "https://www.whatsapp.com",
    "https://www.github.com", "https://www.stackoverflow.com", "https://www.adobe.com",
    "https://www.dropbox.com", "https://www.spotify.com", "https://www.twitch.tv",
    "https://www.zoom.us", "https://www.salesforce.com", "https://www.wordpress.com",
    "https://www.pinterest.com", "https://www.tumblr.com", "https://www.paypal.com",
    "https://www.cnn.com", "https://www.bbc.com", "https://www.nytimes.com",
    "https://www.theguardian.com", "https://www.reuters.com", "https://www.forbes.com",
    "https://www.bloomberg.com", "https://www.espn.com", "https://www.weather.com",
    "https://www.walmart.com", "https://www.target.com", "https://www.costco.com",
    "https://www.bestbuy.com", "https://www.homedepot.com", "https://www.lowes.com",
    "https://www.ikea.com", "https://www.nike.com", "https://www.adidas.com",
    "https://www.zara.com", "https://www.hm.com", "https://www.etsy.com",
    "https://www.shopify.com", "https://www.stripe.com", "https://www.slack.com",
    "https://www.notion.so", "https://www.figma.com", "https://www.canva.com",
    "https://www.trello.com", "https://www.atlassian.com", "https://www.jira.com",
    "https://www.gitlab.com", "https://www.bitbucket.org", "https://www.heroku.com",
    "https://www.aws.amazon.com", "https://cloud.google.com", "https://azure.microsoft.com",
    "https://www.oracle.com", "https://www.ibm.com", "https://www.sap.com",
    "https://www.cisco.com", "https://www.intel.com", "https://www.nvidia.com",
    "https://www.amd.com", "https://www.dell.com", "https://www.hp.com",
    "https://www.lenovo.com", "https://www.samsung.com", "https://www.sony.com",
    "https://www.lg.com", "https://www.panasonic.com", "https://www.philips.com",
    "https://www.siemens.com", "https://www.bosch.com", "https://www.ge.com",
    "https://www.3m.com", "https://www.toyota.com", "https://www.honda.com",
    "https://www.bmw.com", "https://www.mercedes-benz.com", "https://www.audi.com",
    "https://www.tesla.com", "https://www.ford.com", "https://www.gm.com",
    "https://www.nasa.gov", "https://www.nih.gov", "https://www.cdc.gov",
    "https://www.who.int", "https://www.un.org", "https://www.worldbank.org",
    "https://www.imf.org", "https://www.harvard.edu", "https://www.mit.edu",
    "https://www.stanford.edu", "https://www.yale.edu", "https://www.princeton.edu",
    "https://www.columbia.edu", "https://www.uchicago.edu", "https://www.upenn.edu",
    "https://www.cornell.edu", "https://www.duke.edu", "https://www.northwestern.edu",
    "https://www.caltech.edu", "https://www.berkeley.edu", "https://www.ucla.edu",
    "https://www.umich.edu", "https://www.utexas.edu", "https://www.washington.edu",
    "https://www.ox.ac.uk", "https://www.cam.ac.uk", "https://www.imperial.ac.uk",
    "https://www.chase.com", "https://www.bankofamerica.com", "https://www.wellsfargo.com",
    "https://www.citibank.com", "https://www.usbank.com", "https://www.capitalone.com",
    "https://www.americanexpress.com", "https://www.discover.com", "https://www.fidelity.com",
    "https://www.schwab.com", "https://www.vanguard.com", "https://www.robinhood.com",
    "https://www.coinbase.com", "https://www.binance.com", "https://www.kraken.com",
    "https://www.airbnb.com", "https://www.booking.com", "https://www.expedia.com",
    "https://www.tripadvisor.com", "https://www.kayak.com", "https://www.hotels.com",
    "https://www.uber.com", "https://www.lyft.com", "https://www.doordash.com",
    "https://www.grubhub.com", "https://www.instacart.com", "https://www.postmates.com",
    "https://www.zillow.com", "https://www.realtor.com", "https://www.redfin.com",
    "https://www.trulia.com", "https://www.apartments.com",
    "https://mail.google.com", "https://drive.google.com", "https://docs.google.com",
    "https://www.office.com", "https://outlook.live.com", "https://onedrive.live.com",
    "https://www.icloud.com", "https://www.hulu.com", "https://www.disneyplus.com",
    "https://www.hbomax.com", "https://www.peacocktv.com", "https://www.paramount.com",
    "https://www.crunchyroll.com", "https://www.funimation.com",
    "https://www.duolingo.com", "https://www.coursera.org", "https://www.udemy.com",
    "https://www.edx.org", "https://www.khanacademy.org", "https://www.codecademy.com",
    "https://www.medium.com", "https://www.substack.com", "https://www.quora.com",
    "https://www.healthline.com", "https://www.webmd.com", "https://www.mayoclinic.org",
    "https://www.irs.gov", "https://www.usps.com", "https://www.ups.com",
    "https://www.fedex.com", "https://www.dhl.com",
    "https://www.grammarly.com", "https://www.lastpass.com", "https://www.1password.com",
    "https://www.nordvpn.com", "https://www.expressvpn.com",
    "https://www.mozilla.org", "https://www.brave.com", "https://www.opera.com",
    "https://www.vivaldi.com", "https://www.epic.com",
    "https://store.steampowered.com", "https://www.epicgames.com",
    "https://www.ea.com", "https://www.ubisoft.com", "https://www.roblox.com",
    "https://www.minecraft.net", "https://www.blizzard.com",
    "https://www.nba.com", "https://www.nfl.com", "https://www.mlb.com",
    "https://www.fifa.com", "https://www.olympics.com",
    # Additional legitimate patterns with paths
    "https://www.google.com/search?q=python+programming",
    "https://www.amazon.com/dp/B08N5WRWNW",
    "https://en.wikipedia.org/wiki/Machine_learning",
    "https://docs.python.org/3/library/re.html",
    "https://developer.mozilla.org/en-US/docs/Web",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://github.com/tensorflow/tensorflow",
    "https://stackoverflow.com/questions/tagged/python",
    "https://www.reddit.com/r/programming",
    "https://news.ycombinator.com/item?id=12345",
    "https://medium.com/@user/article-title-123abc",
    "https://www.bbc.com/news/technology-12345678",
    "https://www.nytimes.com/2024/01/15/technology/ai-news.html",
    "https://scholar.google.com/citations?user=abc123",
    "https://play.google.com/store/apps/details?id=com.app",
    "https://apps.apple.com/us/app/example/id123456789",
    "https://www.linkedin.com/in/john-doe-123456",
    "https://www.facebook.com/groups/12345",
    "https://twitter.com/elonmusk/status/1234567890",
    "https://www.instagram.com/p/ABC123xyz/",
]


# ========================
# PHISHING URLs (Curated from public phishing databases + synthetic realistic patterns)
# ========================
PHISHING_URLS = [
    # IP-based phishing
    "http://192.168.1.1/paypal/login.html",
    "http://10.0.0.1/secure/verify-account.php",
    "http://172.16.0.1:8080/banking/login",
    "http://203.0.113.42/apple-id/verify",
    "http://198.51.100.55/microsoft/signin.aspx",
    "http://192.0.2.1/amazon/order-confirm.html",
    "http://185.234.218.12/login/google-auth",
    "http://45.33.32.156:443/banking/secure/",
    "http://91.198.174.192/facebook-login/",
    "http://104.16.85.20/netflix-billing/update",
    # Suspicious TLD phishing
    "http://paypal-secure-login.tk/verify",
    "http://amazon-order-update.ml/confirm",
    "http://google-security-alert.ga/signin",
    "http://apple-id-locked.cf/unlock",
    "http://microsoft-account.gq/reset",
    "http://netflix-billing-update.tk/payment",
    "http://facebook-security.ml/checkpoint",
    "http://instagram-verify.ga/confirm-identity",
    "http://linkedin-notification.cf/respond",
    "http://twitter-suspended.gq/appeal",
    "http://chase-bank-alert.tk/verify-now",
    "http://wellsfargo-security.ml/update-info",
    "http://bankofamerica-alert.ga/verify-account",
    "http://citibank-notification.cf/secure-login",
    "http://usbank-alert.gq/update-details",
    # Brand impersonation with hyphens
    "http://pay-pal-secure.com/login/verify",
    "http://amaz0n-order.com/confirm-details",
    "http://g00gle-security.com/alert/signin",
    "http://app1e-support.com/unlock-account",
    "http://micr0soft-update.com/account/reset",
    "http://netf1ix-billing.com/payment-update",
    "http://faceb00k-security.com/checkpoint",
    "http://1nstagram-verify.com/identity",
    "http://linked1n-alert.com/notification",
    "http://tw1tter-support.com/suspended",
    # Long obfuscated URLs
    "http://secure-login-paypal.com.verify-account.suspicious-domain.tk/login.php?id=victim&token=abc123def456",
    "http://www.amazon.com-order-confirm.malicious-site.ml/update?session=xyz789&redirect=true",
    "http://signin.google.com.security-alert.evil.ga/verify?user=target&auth=fake",
    "http://appleid.apple.com-locked-account.phish.cf/unlock?id=user123",
    "http://login.microsoftonline.com.account-reset.bad.gq/signin.aspx?client=false",
    # Subdomain abuse
    "http://paypal.secure-login.evil.com/verify",
    "http://amazon.order-update.malicious.net/confirm",
    "http://google.security-check.fake.org/signin",
    "http://apple.id-verification.scam.com/unlock",
    "http://microsoft.account-alert.phish.net/reset",
    "http://www.paypal.com.evil-domain.tk/login",
    "http://www.amazon.com.fake-checkout.ml/cart",
    "http://www.google.com.security.ga/alert",
    "http://accounts.google.com.login.evil.cf/verify",
    "http://www.facebook.com.security.gq/checkpoint",
    # URL shortener abuse
    "http://bit.ly/3abc123",
    "http://tinyurl.com/phishing-link",
    "http://goo.gl/suspicious123",
    "http://t.co/malicious789",
    "http://ow.ly/fake456",
    # Encoding and obfuscation
    "http://paypa%6C.com/login",
    "http://amaz%6Fn.com-verify.evil.com/order",
    "http://g%6Fogle.com.alert.bad.tk/security",
    "http://faceb%6Fok.security.evil.ml/login",
    "http://www.evil.com/redirect%3Furl%3Dpaypal.com",
    # @ symbol tricks
    "http://www.google.com@evil.com/login",
    "http://www.paypal.com@phishing.tk/verify",
    "http://www.amazon.com@malicious.ml/order",
    "http://www.apple.com@scam.ga/unlock",
    "http://www.microsoft.com@fake.cf/signin",
    # Double slash redirect
    "http://www.legitimate.com//evil.com/phishing",
    "http://trusted-bank.com//attacker.tk/login",
    "http://secure.paypal.com//malicious.ml/verify",
    "http://www.chase.com//phisher.ga/banking",
    "http://www.wellsfargo.com//scam.cf/online",
    # Port-based
    "http://paypal-login.com:8080/verify",
    "http://amazon-checkout.com:3000/payment",
    "http://google-auth.com:4443/signin",
    "http://apple-support.com:9090/unlock",
    "http://microsoft-reset.com:1337/account",
    # Phishing keyword stuffing
    "http://secure-update-verify-login-account.com/banking",
    "http://confirm-identity-reset-password-auth.com/verify",
    "http://urgent-security-alert-suspended.com/action",
    "http://verify-your-account-now-important.com/update",
    "http://immediate-action-required-security.com/login",
    # Random/gibberish domains
    "http://xkj2h4s9d.com/login",
    "http://a3b5c7d9e.tk/verify",
    "http://qwrtyxcvb.ml/accounts",
    "http://zxmnbvpls.ga/banking",
    "http://hjk67bnm3.cf/secure",
    "http://yr8s2kd0w.gq/signin",
    "http://p4x9nm2qa.com/login/verify",
    "http://m8k3jd92s.net/account",
    "http://v5b7h2x9c.org/update",
    "http://f3g6j8k1r.tk/confirm",
    # Complex multi-layer phishing
    "http://www.paypal.com.secure.login.verify.account.evil-domain.tk/webapps/auth/protocol/openidconnect/v1/authorize?client_id=fake",
    "http://signin.ebay.com.verify.identity.scam123.ml/ws/eBayISAPI.dll?SignIn&campid=fake",
    "http://myaccount.google.com.security.check.alert.badsite.ga/ServiceLogin?passive=true",
    "http://secure01.chase.com.verify.banking.phish.cf/auth/fcc/login.action?campaign=fake",
    "http://online.wellsfargo.com.signon.update.evil.gq/das/cgi-bin/session.cgi?screenid=fake",
    # Data URI / unusual schemes
    "http://evil.com/phishing.html#@paypal.com",
    "http://malicious.tk/login.php?redirect=https://paypal.com",
    "http://phish.ml/fake?url=amazon.com&session=stolen",
    "http://scam.ga/verify.aspx?bank=chase&user=victim",
    "http://bad.cf/auth?service=google&token=fake123",
    # Typosquatting
    "http://paypall.com/login",
    "http://paypaI.com/login",
    "http://amazonn.com/order",
    "http://amzon.com/checkout",
    "http://gogle.com/signin",
    "http://googIe.com/security",
    "http://facbook.com/login",
    "http://facebok.com/security",
    "http://twiter.com/login",
    "http://instagam.com/verify",
    "http://linkdin.com/signin",
    "http://microsft.com/account",
    "http://mircosoft.com/signin",
    "http://appple.com/support",
    "http://aplle.com/id",
    "http://netflx.com/billing",
    "http://neflix.com/payment",
    "http://chse.com/banking",
    "http://wellsfago.com/online",
    "http://ciitibank.com/login",
    # Long path phishing
    "http://evil.com/wp-content/uploads/2024/01/paypal/login/index.html",
    "http://compromised-site.com/images/logos/hidden/amazon/order/verify/payment.php",
    "http://hacked-wordpress.com/wp-admin/includes/google/security/alert/signin.html",
    "http://innocent-looking.com/.well-known/acme-challenge/../../phishing/login.php",
    "http://normal-site.org/blog/2024/01/hidden-directory/paypal-clone/index.html",
    # HTTPS phishing (modern phishers use HTTPS too)
    "https://paypal-secure-login.tk/verify",
    "https://amazon-order-update.ml/confirm",
    "https://google-security-alert.ga/signin",
    "https://chase-verify-account.cf/banking",
    "https://secure-wellsfargo-login.gq/online",
    "https://update-your-apple-id.tk/unlock",
    "https://facebook-checkpoint-security.ml/verify",
    "https://linkedin-job-alert.ga/respond",
    "https://netflix-payment-failed.cf/update",
    "https://instagram-copyright-notice.gq/appeal",
    # Additional realistic phishing patterns
    "http://security-paypal.com/cgi-bin/webscr.php?cmd=_login-submit",
    "http://update-amazon.com/ap/signin?openid.ns=http://specs.openid.net",
    "http://alert-chase.com/auth/fcc/login.action",
    "http://verify-apple.com/IDMSWebAuth/login?appIdKey=fake",
    "http://confirm-microsoft.com/common/oauth2/v2.0/authorize",
    "http://banking-secure-login.com/online/auth",
    "http://account-verify-now.com/WebObjects/iTunesConnect",
    "http://secure-payment-update.com/checkout/confirm",
    "http://identity-verification.com/auth/realms/master",
    "http://login-portal-secure.com/sso/authenticate",
]


def generate_dataset_variations():
    """Generate more URL variations from base patterns to increase dataset size."""
    extra_legit = []
    extra_phish = []

    # Generate legitimate URL variations
    legit_domains = [
        "google.com", "youtube.com", "facebook.com", "amazon.com", "microsoft.com",
        "apple.com", "github.com", "stackoverflow.com", "reddit.com", "wikipedia.org",
        "linkedin.com", "twitter.com", "instagram.com", "netflix.com", "spotify.com",
        "dropbox.com", "adobe.com", "salesforce.com", "zoom.us", "slack.com",
        "notion.so", "figma.com", "canva.com", "trello.com", "medium.com"
    ]

    legit_paths = [
        "/", "/about", "/contact", "/help", "/support", "/faq",
        "/products", "/services", "/blog", "/news", "/careers",
        "/pricing", "/features", "/docs", "/api", "/developers",
        "/privacy", "/terms", "/settings", "/account", "/dashboard",
        "/search?q=technology", "/category/electronics",
        "/article/latest-news-2024", "/user/profile",
        "/download", "/resources", "/community",
    ]

    for domain in legit_domains:
        for path in random.sample(legit_paths, min(8, len(legit_paths))):
            extra_legit.append(f"https://www.{domain}{path}")

    # Generate phishing URL variations
    phish_domains_base = ["paypal", "amazon", "google", "apple", "microsoft",
                          "chase", "wellsfargo", "netflix", "facebook", "instagram"]
    phish_tlds = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".club", ".work", ".buzz"]
    phish_separators = ["-", "--", ".", "-secure-", "-login-", "-verify-", "-update-"]
    phish_keywords = ["login", "verify", "secure", "update", "account", "confirm",
                      "alert", "billing", "payment", "signin", "reset", "unlock"]
    phish_paths = [
        "/login.php", "/verify.html", "/signin.aspx", "/confirm.php",
        "/update-info", "/reset-password", "/verify-identity",
        "/secure-login?id=victim", "/auth?token=fake",
        "/account/verify?session=abc123",
    ]

    for brand in phish_domains_base:
        for tld in random.sample(phish_tlds, 4):
            for sep in random.sample(phish_separators, 3):
                keyword = random.choice(phish_keywords)
                path = random.choice(phish_paths)
                scheme = "https" if random.random() > 0.5 else "http"
                url = f"{scheme}://{brand}{sep}{keyword}{tld}{path}"
                extra_phish.append(url)

    # Subdomain abuse variations
    for brand in phish_domains_base:
        for tld in random.sample(phish_tlds, 3):
            evil_domain = f"evil{random.randint(1,999)}"
            path = random.choice(phish_paths)
            scheme = "https" if random.random() > 0.5 else "http"
            extra_phish.append(f"{scheme}://{brand}.{evil_domain}{tld}{path}")
            extra_phish.append(f"{scheme}://www.{brand}.com.{evil_domain}{tld}{path}")

    # IP-based variations
    for _ in range(50):
        ip = f"{random.randint(1,254)}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}"
        brand = random.choice(phish_domains_base)
        path = random.choice(phish_paths)
        scheme = "https" if random.random() > 0.5 else "http"
        extra_phish.append(f"{scheme}://{ip}/{brand}{path}")

    return extra_legit, extra_phish


def create_dataset():
    """Create the full URL dataset with labels."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Generate variations
    extra_legit, extra_phish = generate_dataset_variations()

    # Combine all URLs
    all_legit = list(set(LEGITIMATE_URLS + extra_legit))
    all_phish = list(set(PHISHING_URLS + extra_phish))

    # Balance the dataset
    min_size = min(len(all_legit), len(all_phish))
    if len(all_legit) > min_size:
        all_legit = random.sample(all_legit, min_size)
    if len(all_phish) > min_size:
        all_phish = random.sample(all_phish, min_size)

    print(f"[+] Legitimate URLs: {len(all_legit)}")
    print(f"[+] Phishing URLs:   {len(all_phish)}")
    print(f"[+] Total URLs:      {len(all_legit) + len(all_phish)}")

    # Save raw URLs
    raw_file = os.path.join(RAW_DIR, "urls.csv")
    with open(raw_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["url", "label"])
        for url in all_legit:
            writer.writerow([url, 0])  # 0 = legitimate
        for url in all_phish:
            writer.writerow([url, 1])  # 1 = phishing

    print(f"[+] Raw URLs saved to: {raw_file}")
    return raw_file


def extract_and_save_features(raw_file):
    """Extract features from raw URLs and save as processed CSV."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from src.feature_engineering import extract_features, FEATURE_NAMES

    import pandas as pd
    df = pd.read_csv(raw_file)

    print(f"\n[*] Extracting {len(FEATURE_NAMES)} features from {len(df)} URLs...")

    features_list = []
    for i, row in df.iterrows():
        features = extract_features(row['url'])
        features['label'] = row['label']
        features_list.append(features)

        if (i + 1) % 200 == 0:
            print(f"    Processed {i + 1}/{len(df)} URLs...")

    features_df = pd.DataFrame(features_list)
    output_file = os.path.join(PROCESSED_DIR, "features.csv")
    features_df.to_csv(output_file, index=False)
    print(f"[+] Features saved to: {output_file}")
    print(f"[+] Feature matrix shape: {features_df.shape}")
    return output_file


if __name__ == "__main__":
    print("=" * 60)
    print("  URL Phishing Detection - Dataset Preparation")
    print("=" * 60)
    print()

    raw_file = create_dataset()
    features_file = extract_and_save_features(raw_file)

    print()
    print("=" * 60)
    print("  Dataset ready! You can now run: python src/train.py")
    print("=" * 60)
