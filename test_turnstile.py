import asyncio
import nodriver as uc
import json
import os
import sys
import tempfile

TURNSTILE_SITEKEY = "0x4AAAAAAA1jQEh8YFk064tz"

HTML_PAGE = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
</head>
<body>
    <div id="turnstile-widget"></div>
    <script>
        function onTurnstileCallback(token) {{
            document.title = 'TURNSTILE_TOKEN:' + token;
        }}
        window.addEventListener('load', function() {{
            if (typeof turnstile !== 'undefined') {{
                turnstile.render('#turnstile-widget', {{
                    sitekey: '{TURNSTILE_SITEKEY}',
                    callback: onTurnstileCallback
                }});
            }}
        }});
    </script>
</body>
</html>"""

async def get_turnstile_token(timeout=60):
    html_path = os.path.join(tempfile.gettempdir(), "turnstile_test.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_PAGE)
    
    browser = await uc.start()
    try:
        page = await browser.get("file://" + html_path)
        
        for i in range(timeout // 2):
            await page.sleep(2)
            title = await page.evaluate("document.title")
            if title and title.startswith("TURNSTILE_TOKEN:"):
                token = title.replace("TURNSTILE_TOKEN:", "")
                print(f"Got token ({len(token)} chars): {token[:50]}...")
                return token
            print(f"Waiting for Turnstile... ({i+1}/{timeout//2})")
        
        print("Timeout: no token received")
        return None
    finally:
        await browser.stop()

async def main():
    token = await get_turnstile_token()
    if token:
        # Now test it with the DeepSeek API
        import urllib.request
        os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
        os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
        ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
        opener = urllib.request.build_opener(ph)
        
        import uuid
        payload = json.dumps({
            "email": "dijiaozhibei+test99@gmail.com",
            "scenario": "register",
            "device_id": str(uuid.uuid4()),
            "locale": "en_US",
            "turnstile_token": token,
        }).encode()
        
        req = urllib.request.Request(
            "https://chat.deepseek.com/api/v0/users/create_email_verification_code",
            data=payload, method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        try:
            r = opener.open(req, timeout=30)
            print(f"API Status: {r.status}")
            print(f"API Response: {r.read().decode()[:500]}")
        except urllib.error.HTTPError as e:
            print(f"API Error: {e.code} {e.read().decode()[:500]}")

if __name__ == "__main__":
    asyncio.run(main())
