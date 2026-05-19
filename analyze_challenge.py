import os, re, json
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
import cloudscraper

scraper = cloudscraper.create_scraper()

r = scraper.get("https://raw.githubusercontent.com/dijiaozhibei-top/deepseek-batch-register/refs/heads/main/challenge.js", timeout=15)
if r.status_code == 200 and len(r.text) > 1000:
    js = r.text
elif os.path.exists("challenge.js"):
    with open("challenge.js", "r", encoding="utf-8") as f:
        js = f.read()
else:
    # Download fresh
    r = scraper.get("https://chat.deepseek.com/sign_up", timeout=30)
    m = re.search(r'src="([^"]+challenge\.js[^"]*)"', r.text)
    if m:
        js_url = m.group(1)
        r2 = scraper.get(js_url, timeout=30)
        js = r2.text
        with open("challenge.js", "w", encoding="utf-8") as f:
            f.write(js)

print(f"Challenge JS size: {len(js)} chars")

# Check if it's obfuscated and has specific keywords
keywords = ["SHA", "sha", "hash", "difficulty", "difficulty", "proof", "nonce", "token"]
for kw in keywords:
    if kw in js:
        count = js.count(kw)
        print(f"  {kw}: {count} occurrences")

# Look for the main challenge function
for kw in ["sha256", "sha-256", "SHA256", "hmac", "HMAC", "pow", "PoW", "difficulty", "work"]:
    idx = js.lower().find(kw)
    if idx >= 0:
        print(f"Found '{kw}' at position {idx}: {js[max(0,idx-20):idx+80]}")
