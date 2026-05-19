import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
import requests
import cloudscraper

scraper = cloudscraper.create_scraper()
r = scraper.get("https://chat.deepseek.com/sign_up", timeout=30)
print("Status:", r.status_code)
print("Length:", len(r.text))
print("x-amzn-waf-action:", r.headers.get("x-amzn-waf-action"))
print("Cookies:", dict(r.cookies))

if r.status_code == 200:
    print("SUCCESS! Page loaded")
    print(r.text[:1000])
elif r.status_code == 202:
    print("AWS WAF challenge")
    # The actual challenge JS is in the response
    # cloudscraper might have already solved it
    print("Response snippet:", r.text[:2000])
