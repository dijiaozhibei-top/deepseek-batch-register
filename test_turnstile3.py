import asyncio
import nodriver as uc

async def main():
    # Start browser with proxy
    browser = await uc.start(
        browser_executable_path=None,
        headless=True,
        additional_arguments=[
            "--proxy-server=http://127.0.0.1:10810",
            "--disable-blink-features=AutomationControlled",
        ]
    )
    
    # Navigate to DeepSeek sign_up page
    page = await browser.get("https://chat.deepseek.com/sign_up")
    await page.sleep(5)
    
    title = await page.evaluate("document.title")
    html = await page.get_content()
    print(f"Title: {title}")
    
    if "ERROR" in html[:500] and "request could not be satisfied" in html[:500]:
        print("BLOCKED BY CLOUDFLARE")
    else:
        print("PAGE LOADED")
        # Check for Turnstile
        has_cf = await page.evaluate("document.getElementById('cf-turnstile') !== null")
        print(f"Has cf-turnstile element: {has_cf}")
        
        has_turnstile = await page.evaluate("typeof turnstile !== 'undefined'")
        print(f"Has turnstile object: {has_turnstile}")
        
        # Look for Turnstile input
        for i in range(20):
            await page.sleep(3)
            token = await page.evaluate("""
                () => {
                    const input = document.querySelector('[name="cf-turnstile-response"]');
                    return input ? input.value : null;
                }
            """)
            if token:
                print(f"TOKEN FOUND: {token[:50]}...")
                
                # Use it to call the API
                import json, urllib.request, uuid
                ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
                opener = urllib.request.build_opener(ph)
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
                    headers={"Content-Type": "application/json"}
                )
                try:
                    r = opener.open(req, timeout=30)
                    print(f"API Status: {r.status}")
                    print(f"API Response: {r.read().decode()[:500]}")
                except urllib.error.HTTPError as e:
                    print(f"API Error: {e.code} {e.read().decode()[:500]}")
                break
            
            print(f"Waiting for token... ({i+1}/20)")
    
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
