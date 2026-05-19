import asyncio
import nodriver as uc

async def main():
    browser = await uc.start(
        headless=False,
        additional_arguments=["--disable-blink-features=AutomationControlled"]
    )
    
    print("Loading sign_up page...")
    page = await browser.get("https://chat.deepseek.com/sign_up")
    await page.sleep(10)
    
    title = await page.evaluate("document.title")
    html = await page.get_content()
    print(f"Title: {title}")
    print(f"Page loaded: {len(html)} chars")
    
    # Check if we got the real page or WAF
    if "challenge-container" in html or "awsWafCookieDomainList" in html:
        print("AWS WAF CHALLENGE PAGE - waiting for auto-solve...")
        for i in range(30):
            await page.sleep(2)
            html2 = await page.get_content()
            if "challenge-container" not in html2 and "awsWafCookieDomainList" not in html2:
                print(f"WAF solved after {i+1} iterations!")
                html = html2
                break
        else:
            print("WAF challenge not solved after 60 seconds")
    
    # Check what we have
    if "cf-turnstile" in html or "turnstile" in html:
        print("Turnstile widget found!")
    if "email" in html.lower():
        import re
        emails = re.findall(r'<input[^>]*email[^>]*>', html, re.IGNORECASE)
        print(f"Email inputs found: {len(emails)}")
    if "请输入邮箱地址" in html or "Email" in html:
        print("Registration form detected")
    
    print(f"First 1000 chars of HTML: {html[:1000]}")
    
    input("Press Enter to close browser...")
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
