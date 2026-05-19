import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
import undetected_chromedriver as uc
import time
import re

options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--headless=new")
options.add_argument("--proxy-server=socks5://127.0.0.1:10810")

driver = uc.Chrome(options=options)

# Set Accept-Language header via CDP
driver.execute_cdp_cmd("Network.enable", {})
driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
    "headers": {"Accept-Language": "en-US,en;q=0.9"}
})

driver.get("https://chat.deepseek.com/sign_up")
time.sleep(8)

print(f"Title: {driver.title}")
html = driver.page_source

for m in re.finditer(r'<meta[^>]*name="(?:ip|region)"[^>]*>', html):
    print(f"Meta: {m.group()}")

if "email" in html.lower():
    print("Email form found!")
    inputs = driver.find_elements("tag name", "input")
    for inp in inputs:
        t = inp.get_attribute("type") or ""
        p = inp.get_attribute("placeholder") or ""
        n = inp.get_attribute("name") or ""
        print(f"  Input: type={t}, name={n}, placeholder={p}")
else:
    print("Phone form (CN version) detected")

# Also check with HTTP proxy (not SOCKS5) in case proxy is HTTP
driver.quit()

# Try again with HTTP proxy
print("\n\n--- Retrying with HTTP proxy ---")
options2 = uc.ChromeOptions()
options2.add_argument("--disable-blink-features=AutomationControlled")
options2.add_argument("--no-sandbox")
options2.add_argument("--disable-dev-shm-usage")
options2.add_argument("--window-size=1920,1080")
options2.add_argument("--headless=new")
options2.add_argument("--proxy-server=http://127.0.0.1:10810")

driver2 = uc.Chrome(options=options2)
driver2.execute_cdp_cmd("Network.enable", {})
driver2.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
    "headers": {"Accept-Language": "en-US,en;q=0.9"}
})
driver2.get("https://chat.deepseek.com/sign_up")
time.sleep(8)

print(f"Title: {driver2.title}")
html2 = driver2.page_source
for m in re.finditer(r'<meta[^>]*name="(?:ip|region)"[^>]*>', html2):
    print(f"Meta: {m.group()}")

if "email" in html2.lower():
    print("Email form found!")
else:
    print("Phone form (CN version) detected")

driver2.quit()
