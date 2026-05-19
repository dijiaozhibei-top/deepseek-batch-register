import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
import undetected_chromedriver as uc
import time
import json
import uuid
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)

options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--headless=new")
options.add_argument("--lang=en-US")

driver = uc.Chrome(options=options)

# Intercept network requests
turnstile_token = None
api_success = None

print("Loading sign_up page...")
driver.get("https://chat.deepseek.com/sign_up")
time.sleep(5)

print(f"Title: {driver.title}")

# Check if page loaded
html = driver.page_source
if "sign_in" in html.lower() or "sign up" in html.lower() or "email" in html.lower() or "deepseek" in html.lower():
    print("Page loaded successfully")
else:
    print(f"Page content preview: {html[:500]}")

# Find and fill email input
try:
    # Try different selectors for the email input
    email_input = None
    for selector in ["input[type='email']", "input[name='email']", "input[placeholder*='Email']", "input[placeholder*='email']"]:
        try:
            email_input = driver.find_element("css selector", selector)
            break
        except:
            pass
    
    if not email_input:
        # Try getting all inputs
        inputs = driver.find_elements("tag name", "input")
        print(f"Found {len(inputs)} input fields")
        for inp in inputs:
            p = inp.get_attribute("placeholder") or ""
            n = inp.get_attribute("name") or ""
            t = inp.get_attribute("type") or ""
            print(f"  Input: type={t}, name={n}, placeholder={p}")
        
        # Try aria labels
        for inp in inputs:
            label = inp.get_attribute("aria-label") or ""
            if "email" in label.lower():
                email_input = inp
                break
    
    if email_input:
        email_input.clear()
        email_input.send_keys("dijiaozhibei+test99@gmail.com")
        print("Email filled!")
    else:
        print("Could not find email input!")
        print("Page source snippet:", driver.page_source[:3000])

except Exception as e:
    print(f"Error finding email input: {e}")

# Look for the send code button
try:
    # Try various button selectors
    for selector in ["button[type='submit']", "button:contains('Send')", "button"]:
        try:
            buttons = driver.find_elements("tag name", "button")
            for btn in buttons:
                text = btn.text
                if "send" in text.lower() or "code" in text.lower() or "verification" in text.lower():
                    print(f"Found button: '{text}'")
                    btn.click()
                    print("Clicked send code button!")
                    break
        except:
            pass
except Exception as e:
    print(f"Error clicking button: {e}")

# Wait for Turnstile to appear
print("Waiting for Turnstile...")
for i in range(30):
    time.sleep(2)
    
    has_turnstile = driver.execute_script("return typeof turnstile !== 'undefined' && turnstile !== null")
    if has_turnstile:
        print(f"Turnstile available! (iteration {i+1})")
        
        # Get token
        token = driver.execute_script("""
            return new Promise((resolve) => {
                try {
                    const div = document.createElement('div');
                    div.id = 'cf-turnstile-extract';
                    div.style.display = 'none';
                    document.body.appendChild(div);
                    turnstile.render('#cf-turnstile-extract', {
                        sitekey: '0x4AAAAAAA1jQEh8YFk064tz',
                        callback: function(token) { resolve(token); },
                        'error-callback': function(e) { resolve(null); }
                    });
                } catch(e) { resolve(null); }
            })
        """)
        if token:
            print(f"TOKEN ({len(token)} chars): {token[:50]}...")
            
            # Use the token for the API
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
                print(f"API: {r.status} {r.read().decode()[:500]}")
            except urllib.error.HTTPError as e:
                print(f"API Error: {e.code} {e.read().decode()[:500]}")
            
            break
    
    print(f"  Waiting... ({i+1}/30)")

driver.quit()
