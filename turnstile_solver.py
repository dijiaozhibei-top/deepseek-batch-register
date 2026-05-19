import asyncio
import logging
import nodriver as uc

logger = logging.getLogger(__name__)

TURNSTILE_SITEKEY = "0x4AAAAAAA1jQEh8YFk064tz"
SIGNUP_URL = "https://chat.deepseek.com/sign_up"


async def get_turnstile_token(max_wait: int = 90) -> str | None:
    browser = None
    try:
        browser = await uc.start(
            headless=True,
            additional_arguments=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080",
            ],
        )

        page = await browser.get(SIGNUP_URL)
        await page.sleep(8)

        for i in range(max_wait // 3):
            await page.sleep(3)

            try:
                html = await page.get_content()
            except Exception:
                continue

            if "ERROR" in html[:500] and "request could not be satisfied" in html[:500]:
                logger.error("Cloudflare WAF blocked the page")
                return None

            has_turnstile = await page.evaluate(
                "typeof turnstile !== 'undefined' && turnstile !== null"
            )
            if not has_turnstile:
                continue

            token = await page.evaluate(f"""
                () => new Promise((resolve) => {{
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
    finally:
        if browser:
            try:
                await browser.stop()
            except Exception:
                pass


def solve_turnstile(max_wait: int = 90) -> str | None:
    """Synchronous wrapper for get_turnstile_token."""
    try:
        return asyncio.run(get_turnstile_token(max_wait))
    except RuntimeError as e:
        # Handle case where event loop is already running
        logger.warning(f"Event loop conflict, trying new loop: {e}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(get_turnstile_token(max_wait))
        finally:
            loop.close()
