import urllib.request, json, uuid

# Test 1: urllib - bare request
print("=== Test 1: urllib (bare) ===")
try:
    r = urllib.request.urlopen("https://chat.deepseek.com/sign_up", timeout=15)
    print(f"Status: {r.status}")
    print(f"First 500: {r.read().decode()[:500]}")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    body = e.read().decode()[:500]
    if "request could not be satisfied" in body or "ERROR" in body[:200]:
        print("CLOUDFLARE BLOCK PAGE")
    else:
        print(f"Body: {body}")

# Test 2: urllib with browser headers
print()
print("=== Test 2: urllib (Chrome UA) ===")
try:
    req = urllib.request.Request(
        "https://chat.deepseek.com/sign_up",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    r = urllib.request.urlopen(req, timeout=15)
    print(f"Status: {r.status}")
    print(f"First 500: {r.read().decode()[:500]}")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    body = e.read().decode()[:500]
    if "request could not be satisfied" in body or "ERROR" in body[:200]:
        print("CLOUDFLARE BLOCK PAGE")
    else:
        print(f"Body: {body}")

# Test 3: cloudscraper
print()
print("=== Test 3: cloudscraper ===")
try:
    import cloudscraper
    scraper = cloudscraper.create_scraper()
    r = scraper.get("https://chat.deepseek.com/sign_up", timeout=30)
    print(f"Status: {r.status_code}")
    print(f"x-amzn-waf-action: {r.headers.get('x-amzn-waf-action')}")
    page = r.text[:500]
    if "request could not be satisfied" in page or "ERROR" in page[:200]:
        print("CLOUDFLARE BLOCK PAGE")
    elif "awsWafCookieDomainList" in page or "challenge" in page.lower()[:200]:
        print("AWS WAF CHALLENGE PAGE")
    else:
        print(f"First 500: {page}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: API endpoint
print()
print("=== Test 4: API endpoint ===")
try:
    payload = json.dumps({
        "email": "test@test.com",
        "scenario": "register",
        "device_id": str(uuid.uuid4()),
        "locale": "en_US",
        "turnstile_token": "",
    }).encode()
    req = urllib.request.Request(
        "https://chat.deepseek.com/api/v0/users/create_email_verification_code",
        data=payload, method="POST",
        headers={"Content-Type": "application/json"}
    )
    r = urllib.request.urlopen(req, timeout=15)
    print(f"Status: {r.status}")
    print(f"Body: {r.read().decode()[:300]}")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    print(f"Body: {e.read().decode()[:300]}")

# Test 5: curl_cffi
print()
print("=== Test 5: curl_cffi ===")
try:
    from curl_cffi import requests as curl_req
    r = curl_req.get("https://chat.deepseek.com/sign_up", impersonate="chrome131", timeout=30)
    print(f"Status: {r.status_code}")
    print(f"First 500: {r.text[:500]}")
except ImportError:
    print("curl_cffi not installed")
except Exception as e:
    print(f"Error: {e}")
