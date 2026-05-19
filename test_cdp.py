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

driver = uc.Chrome(options=options)

# Set Accept-Language header via CDP
driver.execute_cdp_cmd("Network.enable", {})
driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
    "headers": {
        "Accept-Language": "en-US,en;q=0.9",
    }
})

driver.get("https://chat.deepseek.com/sign_up")
time.sleep(5)

print(f"Title: {driver.title}")

# Check the IP/region meta tags
html = driver.page_source
import re
for m in re.finditer(r'<meta[^>]*name="(?:ip|region)"[^>]*>', html):
    print(f"Meta: {m.group()}")

# Check for email input vs phone input
if "email" in html.lower() or "Email" in html:
    print("Email form detected!")
else:
    print("No email form - checking inputs")
    inputs = driver.find_elements("tag name", "input")
    for inp in inputs:
        t = inp.get_attribute("type") or ""
        p = inp.get_attribute("placeholder") or ""
        n = inp.get_attribute("name") or ""
        print(f"  Input: type={t}, name={n}, placeholder={p}")

driver.quit()
