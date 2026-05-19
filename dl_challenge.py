import os, re
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
import cloudscraper

scraper = cloudscraper.create_scraper()
r = scraper.get("https://chat.deepseek.com/sign_up", timeout=30)

m = re.search(r'src="([^"]+challenge\.js[^"]*)"', r.text)
if m:
    js_url = m.group(1)
    print(f"Challenge JS URL: {js_url}")
    r2 = scraper.get(js_url, timeout=30)
    with open("challenge.js", "w", encoding="utf-8") as f:
        f.write(r2.text)
    print(f"Downloaded challenge.js: {len(r2.text)} chars")
    print(f"First 500 chars: {r2.text[:500]}")
else:
    print("No challenge.js found")
    print(r.text[:500])
