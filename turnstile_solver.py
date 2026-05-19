import asyncio
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

        driver.get(SIGNUP_URL)
        driver.implicitly_wait(10)

        import time
        time.sleep(5)

        html = driver.page_source
        if "ERROR" in html[:500] and "request could not be satisfied" in html[:500]:
            logger.error("Cloudflare WAF blocked the page")
            return None

        for i in range(max_wait // 3):
            time.sleep(3)

            has_turnstile = driver.execute_script(
                "return typeof turnstile !== 'undefined' && turnstile !== null"
            )
            if not has_turnstile:
                continue

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

            logger.debug(f"Waiting for Turnstile... ({i+1}/{max_wait//3})")

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
