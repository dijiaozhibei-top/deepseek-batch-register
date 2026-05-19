import logging
import time
import undetected_chromedriver as uc
import json
import uuid
import urllib.request
import os

logger = logging.getLogger(__name__)

TURNSTILE_SITEKEY = "0x4AAAAAAA1jQEh8YFk064tz"
SIGNUP_URL = "https://chat.deepseek.com/sign_up"


def solve_turnstile(max_wait: int = 90) -> str | None:
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--headless=new")

        driver = uc.Chrome(options=options)

        # Set Accept-Language to get English version
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
            "headers": {"Accept-Language": "en-US,en;q=0.9"}
        })

        driver.get(SIGNUP_URL)

        # Wait for page to fully load (AWS WAF challenge -> real page -> Turnstile)
        for i in range(max_wait // 2):
            time.sleep(2)

            title = driver.title
            html = driver.page_source

            # Stage 1: AWS WAF challenge (title is empty)
            if not title or "awsWafCookie" in html or "challenge.js" in html:
                logger.info(f"AWS WAF solving... ({i+1}/{max_wait//2})")
                continue

            # Stage 2: Real DeepSeek page loaded
            if "DeepSeek" in title or "deepseek" in html.lower():
                # Check if Turnstile is available
                has_turnstile = driver.execute_script(
                    "return typeof turnstile !== 'undefined' && turnstile !== null"
                )
                if not has_turnstile:
                    logger.info(f"Page loaded but Turnstile not ready yet ({i+1}/{max_wait//2})")
                    continue

                # Turnstile available - render widget and get token
                token = driver.execute_script(f"""
                    return new Promise((resolve) => {{
                        try {{
                            const div = document.createElement('div');
                            div.id = 'cf-turnstile-solver';
                            div.style.display = 'none';
                            document.body.appendChild(div);
                            turnstile.render('#cf-turnstile-solver', {{
                                sitekey: '{TURNSTILE_SITEKEY}',
                                callback: function(token) {{
                                    resolve(token);
                                }},
                                'error-callback': function(e) {{
                                    resolve(null);
                                }}
                            }});
                        }} catch(e) {{
                            resolve(null);
                        }}
                    }})
                """)

                if token:
                    logger.info(f"Got Turnstile token ({len(token)} chars)")
                    return token

                logger.debug(f"Waiting for Turnstile token... ({i+1}/{max_wait//2})")
            else:
                logger.debug(f"Current title: '{title}' ({i+1}/{max_wait//2})")

        logger.error("Timed out waiting for Turnstile token")
        return None

    except Exception as e:
        logger.error(f"Turnstile solver error: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
