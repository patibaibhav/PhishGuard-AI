/**
 * PhishGuard AI — Client-Side JavaScript
 * Handles URL scanning, animations, and result rendering.
 */

// =====================
// STATE
// =====================

let isScanning = false;

// =====================
// ELEMENTS
// =====================

const scannerForm = document.getElementById('scanner-form');
const urlInput = document.getElementById('url-input');
const scanBtn = document.getElementById('scan-btn');
const inputWrapper = document.getElementById('input-wrapper');
const scannerSection = document.getElementById('scanner-section');
const scanningOverlay = document.getElementById('scanning-overlay');
const scanningSteps = document.getElementById('scanning-steps');
const resultsSection = document.getElementById('results-section');

// Result elements
const verdictCard = document.getElementById('verdict-card');
const verdictIcon = document.getElementById('verdict-icon');
const verdictLabel = document.getElementById('verdict-label');
const verdictUrl = document.getElementById('verdict-url');
const ringFill = document.getElementById('ring-fill');
const confNumber = document.getElementById('conf-number');
const riskFill = document.getElementById('risk-fill');
const riskIndicator = document.getElementById('risk-indicator');
const riskLevelText = document.getElementById('risk-level-text');
const riskFactorsCard = document.getElementById('risk-factors-card');
const riskList = document.getElementById('risk-list');
const featuresGrid = document.getElementById('features-grid');
const featureCount = document.getElementById('feature-count');

// Probability bars
const probBarSafe = document.getElementById('prob-bar-safe');
const probBarPhishing = document.getElementById('prob-bar-phishing');
const probValueSafe = document.getElementById('prob-value-safe');
const probValuePhishing = document.getElementById('prob-value-phishing');


// =====================
// FORM SUBMISSION
// =====================

scannerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url || isScanning) return;
    await scanURL(url);
});

function testURL(url) {
    urlInput.value = url;
    scanURL(url);
}


// =====================
// QR CODE UPLOAD
// =====================

const qrUpload = document.getElementById('qr-upload');
const qrBtn = document.querySelector('.qr-btn');

if (qrUpload) {
    qrUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Visual feedback
        const originalIcon = qrBtn.innerHTML;
        qrBtn.innerHTML = `
            <svg class="spinner" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
            </svg>
        `;
        qrBtn.classList.add('loading-qr');
        urlInput.value = 'Decoding QR Code...';
        urlInput.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/scan-qr', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success && data.url) {
                // Populate the input with the decoded URL
                urlInput.value = data.url;
                urlInput.disabled = false;
                
                // Automatically scan the decoded URL
                await scanURL(data.url);
            } else {
                urlInput.value = '';
                urlInput.disabled = false;
                alert('QR code error: ' + (data.error || 'Could not decode QR.'));
            }
        } catch (err) {
            console.error(err);
            urlInput.value = '';
            urlInput.disabled = false;
            alert('Failed to connect to server for QR decoding.');
        } finally {
            // Restore icon
            qrBtn.innerHTML = originalIcon;
            qrBtn.classList.remove('loading-qr');
            // Clear file input so same file can be selected again if needed
            qrUpload.value = '';
        }
    });
}


// =====================
// MAIN SCAN FUNCTION
// =====================

async function scanURL(url) {
    if (isScanning) return;
    isScanning = true;

    // Reset state
    resultsSection.style.display = 'none';
    inputWrapper.classList.remove('safe-glow', 'danger-glow');

    // Show scanning animation
    scanBtn.classList.add('loading');
    scanningOverlay.classList.add('active');

    // Animate scanning steps
    const steps = scanningSteps.querySelectorAll('.scan-step');
    steps.forEach(s => { s.classList.remove('active', 'done'); });

    await animateStep(steps[0], 400);
    await animateStep(steps[1], 400);

    try {
        // Make prediction request
        steps[2].classList.add('active');
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        steps[2].classList.remove('active');
        steps[2].classList.add('done');
        await sleep(300);

        // Hide scanner, show results
        scanningOverlay.classList.remove('active');
        scanBtn.classList.remove('loading');

        if (data.success) {
            renderResults(data);
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        scanningOverlay.classList.remove('active');
        scanBtn.classList.remove('loading');
        alert('Connection error. Make sure the Flask server is running.');
        console.error(err);
    }

    isScanning = false;
}


function animateStep(step, delay) {
    return new Promise(resolve => {
        step.classList.add('active');
        setTimeout(() => {
            step.classList.remove('active');
            step.classList.add('done');
            resolve();
        }, delay);
    });
}


// =====================
// RENDER RESULTS
// =====================

function renderResults(data) {
    const isPhishing = data.is_phishing;
    const confidence = data.confidence;
    const phishProb = data.phishing_probability;
    const legitProb = data.legitimate_probability;

    // ---- Verdict Card ----
    verdictCard.className = `verdict-card ${isPhishing ? 'danger' : 'safe'}`;
    verdictIcon.innerHTML = isPhishing ? '🚨' : '✅';
    verdictLabel.textContent = isPhishing ? 'Phishing Detected!' : 'URL is Safe';
    verdictUrl.textContent = data.url;

    // Input glow
    inputWrapper.classList.add(isPhishing ? 'danger-glow' : 'safe-glow');

    // ---- Confidence Ring ----
    const circumference = 2 * Math.PI * 52; // r=52
    const offset = circumference - (confidence / 100) * circumference;
    setTimeout(() => {
        ringFill.style.strokeDashoffset = offset;
    }, 100);

    // Animate confidence number
    animateCounter(confNumber, 0, Math.round(confidence), 1200);

    // ---- Risk Meter ----
    const riskPercent = phishProb;
    setTimeout(() => {
        riskIndicator.style.left = riskPercent + '%';
    }, 200);

    const riskLevel = data.risk_level;
    riskLevelText.textContent = riskLevel;
    riskLevelText.style.color = getRiskColor(riskLevel);

    // ---- Risk Factors ----
    if (data.risk_factors && data.risk_factors.length > 0) {
        riskFactorsCard.style.display = 'block';
        riskList.innerHTML = '';
        data.risk_factors.forEach((factor, i) => {
            const li = document.createElement('li');
            li.style.animationDelay = `${i * 0.1}s`;
            li.innerHTML = `<span class="risk-icon">⚠</span> ${escapeHTML(factor)}`;
            riskList.appendChild(li);
        });
    } else {
        riskFactorsCard.style.display = 'none';
    }

    // ---- Feature Analysis ----
    const features = data.features || {};
    const featureKeys = Object.keys(features);
    featureCount.textContent = `${featureKeys.length} features`;
    featuresGrid.innerHTML = '';

    featureKeys.forEach(key => {
        const value = features[key];
        const div = document.createElement('div');
        div.className = 'feature-item';

        const isHighlight = isHighlightFeature(key, value);
        const valueClass = isHighlight ? 'highlight' : (isSafeFeature(key, value) ? 'normal' : '');

        div.innerHTML = `
            <span class="feature-name">${formatFeatureName(key)}</span>
            <span class="feature-value ${valueClass}">${formatFeatureValue(value)}</span>
        `;
        featuresGrid.appendChild(div);
    });

    // ---- Probability Bars ----
    setTimeout(() => {
        probBarSafe.style.width = legitProb + '%';
        probBarPhishing.style.width = phishProb + '%';
    }, 300);
    probValueSafe.textContent = legitProb.toFixed(1) + '%';
    probValuePhishing.textContent = phishProb.toFixed(1) + '%';

    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


// =====================
// UTILITIES
// =====================

function animateCounter(element, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease-out
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + range * eased);

        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}


function getRiskColor(level) {
    const colors = {
        'Safe': '#10b981',
        'Low Risk': '#84cc16',
        'Medium Risk': '#f59e0b',
        'High Risk': '#f97316',
        'Dangerous': '#ef4444',
    };
    return colors[level] || '#9393a8';
}


function isHighlightFeature(key, value) {
    const dangerousIf = {
        'has_ip_address': v => v === 1,
        'suspicious_tld': v => v === 1,
        'has_phishing_keywords': v => v > 1,
        'num_at_symbol': v => v > 0,
        'has_shortener': v => v === 1,
        'has_redirect': v => v === 1,
        'has_port': v => v === 1,
        'has_encoding': v => v === 1,
        'num_subdomains': v => v > 3,
        'url_length': v => v > 75,
        'shannon_entropy': v => v > 4.5,
    };

    return dangerousIf[key] ? dangerousIf[key](value) : false;
}


function isSafeFeature(key, value) {
    if (key === 'has_https' && value === 1) return true;
    if (key === 'has_ip_address' && value === 0) return true;
    if (key === 'suspicious_tld' && value === 0) return true;
    return false;
}


function formatFeatureName(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()).replace(/Url/g, 'URL').replace(/Tld/g, 'TLD').replace(/Ip/g, 'IP');
}


function formatFeatureValue(value) {
    if (typeof value === 'number') {
        if (Number.isInteger(value)) return value.toString();
        return value.toFixed(4);
    }
    return String(value);
}


function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


// =====================
// TOGGLE FEATURES
// =====================

function toggleFeatures() {
    const body = document.getElementById('features-body');
    const chevron = document.getElementById('features-chevron');
    body.classList.toggle('open');
    chevron.classList.toggle('open');
}


// =====================
// RESET
// =====================

function resetScanner() {
    resultsSection.style.display = 'none';
    inputWrapper.classList.remove('safe-glow', 'danger-glow');
    urlInput.value = '';
    urlInput.focus();

    // Reset ring
    ringFill.style.strokeDashoffset = 326.73;
    confNumber.textContent = '0';

    // Reset risk meter
    riskIndicator.style.left = '0%';

    // Reset probability bars
    probBarSafe.style.width = '0%';
    probBarPhishing.style.width = '0%';

    // Reset features
    const body = document.getElementById('features-body');
    body.classList.remove('open');

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}


// =====================
// KEYBOARD SHORTCUT
// =====================

document.addEventListener('keydown', (e) => {
    // Ctrl+K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        urlInput.focus();
    }
});


// =====================
// INIT
// =====================

urlInput.focus();
