import asyncio
import nodriver as uc

async def main():
    browser = await uc.start()
    
    # Try loading the DeepSeek sign_up page WITHOUT proxy (China IP)
    page = await browser.get("https://chat.deepseek.com/sign_up")
    
    for i in range(30):
        await page.sleep(2)
        title = await page.evaluate("document.title")
        html_snippet = await page.evaluate("document.body ? document.body.innerText.substring(0, 500) : 'no body'")
        print(f"[{i+1}] Title: {title}")
        
        # Check for Turnstile token
        token = await page.evaluate("""
            () => {
                const input = document.querySelector('[name="cf-turnstile-response"]');
                return input ? input.value : null;
            }
        """)
        if token:
            print(f"TURNSTILE TOKEN FOUND: {token[:50]}...")
            break
        
        # Check for error
        if "ERROR" in html_snippet or "request could not be satisfied" in html_snippet:
            print(f"BLOCKED BY CLOUDFLARE")
            break
        
        if "sign_up" in html_snippet.lower() or "email" in html_snippet.lower():
            print(f"PAGE LOADED - content: {html_snippet[:200]}")
    else:
        print(f"Final content: {html_snippet[:300]}")
    
    # Also print full HTML for analysis
    html = await page.get_content()
    if "cf-turnstile" in html or "turnstile" in html:
        print("Turnstile widget found in page")
    if "0x4" in html:
        import re
        for m in re.finditer(r'0x[A-Fa-f0-9]{10,}', html):
            print(f"Sitekey found: {m.group()}")
    
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
