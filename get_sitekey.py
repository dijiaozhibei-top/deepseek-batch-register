import urllib.request, os, re

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
opener = urllib.request.build_opener(ph)
r = opener.open(urllib.request.Request("https://chat.deepseek.com/sign_up", headers={"User-Agent": "Mozilla/5.0"}), timeout=15)
html = r.read().decode("utf-8", errors="replace")

for m in re.finditer(r'(?:sitekey|data-sitekey|turnstile_key|cf-turnstile)[=:]\s*["\']([^"\']+)["\']', html, re.IGNORECASE):
    print(f"Found: {m.group(0)}")
    print(f"Value: {m.group(1)}")

# Search for turnstile-related JS
for m in re.finditer(r'turnstile[^<]{0,300}', html, re.IGNORECASE):
    print(f"Turnstile ref: {m.group(0)[:200]}")

# Search for captcha/turnstile keywords
for kw in ["turnstile", "captcha", "recaptcha", "hcaptcha", "cf-turnstile"]:
    if kw in html.lower():
        idx = html.lower().find(kw)
        print(f"Found '{kw}' at position {idx}: {html[max(0,idx-50):idx+150]}")
