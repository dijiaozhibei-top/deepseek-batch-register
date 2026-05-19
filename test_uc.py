import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
import undetected_chromedriver as uc
import time

options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--headless=new")
options.add_argument("--lang=en-US")
options.add_argument("--accept-lang=en-US,en;q=0.9")

driver = uc.Chrome(options=options)
driver.get("https://chat.deepseek.com/sign_up")
time.sleep(8)

html = driver.page_source
title = driver.title
print(f"Title: {title}")
print(f"Page size: {len(html)}")

# Check for WAF
if "AWS" in html or "challenge" in html.lower() or "awsWaf" in html:
    print("AWS WAF challenge detected")
elif "ERROR" in html[:500] and "request could not be satisfied" in html[:500]:
    print("Cloudflare WAF blocked")
else:
    print("Page loaded!")
    # Check for Turnstile
    has_turnstile = driver.execute_script("return typeof turnstile !== 'undefined' && turnstile !== null")
    print(f"Has Turnstile: {has_turnstile}")
    
    # Try to get a token
    if has_turnstile:
        token = driver.execute_script("""
            return new Promise((resolve) => {
                try {
                    const div = document.createElement('div');
                    div.id = 'cf-turnstile-local';
                    div.style.display = 'none';
                    document.body.appendChild(div);
                    turnstile.render('#cf-turnstile-local', {
                        sitekey: '0x4AAAAAAA1jQEh8YFk064tz',
                        callback: function(token) { resolve(token); },
                        'error-callback': function(e) { resolve(null); }
                    });
                } catch(e) { resolve(null); }
            })
        """)
        if token:
            print(f"Got token ({len(token)} chars): {token[:50]}...")
        else:
            # Wait more
            for i in range(10):
                time.sleep(3)
                token = driver.execute_script("return window.__cf_token || null")
                if token:
                    break
                # Try the div again
                token = driver.execute_script("""
                    return new Promise((resolve) => {
                        try {
                            turnstile.render('#cf-turnstile-local', {
                                sitekey: '0x4AAAAAAA1jQEh8YFk064tz',
                                callback: function(token) { resolve(token); },
                                'error-callback': function(e) { resolve(null); }
                            });
                        } catch(e) { resolve(null); }
                    })
                """)
                if token:
                    break
                print(f"Waiting... ({i+1}/10)")

# Look for email input or registration form
for elem_name in ["email", "Email", "emailInput", "email-input"]:
    try:
        elem = driver.find_element("name", elem_name)
        print(f"Found element: name={elem_name}, tag={elem.tag_name}")
    except:
        pass

# Search for email input in page source
import re
for m in re.finditer(r'<input[^>]*email[^>]*>', html, re.IGNORECASE):
    print(f"Email input found: {m.group()[:200]}")

driver.quit()
