import asyncio
import nodriver as uc

async def main():
    browser = await uc.start()
    page = await browser.get("https://chat.deepseek.com/sign_up")
    await page.sleep(5)
    html = await page.get_content()
    if "ERROR" in html and "request could not be satisfied" in html:
        print("BLOCKED by Cloudflare")
    else:
        print("PAGE LOADED SUCCESSFULLY")
        # Try to get token
        for i in range(30):
            await page.sleep(2)
            token = await page.evaluate("""
                () => {
                    const input = document.querySelector('[name="cf-turnstile-response"]');
                    return input ? input.value : null;
                }
            """)
            if token:
                print(f"Token found ({len(token)} chars): {token[:50]}...")
                break
            print(f"Waiting for token... ({i+1}/30)")

    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
