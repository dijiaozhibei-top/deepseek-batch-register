import asyncio
import logging
import nodriver as uc

logger = logging.getLogger(__name__)

TURNSTILE_SITEKEY = "0x4AAAAAAA1jQEh8YFk064tz"


class TurnstileSolver:
    def __init__(self):
        self.browser = None

    async def _ensure_browser(self):
        if self.browser is None:
            self.browser = await uc.start(
                headless=True,
                additional_arguments=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080",
                ],
            )

    async def get_token(self, max_wait: int = 60) -> str | None:
        await self._ensure_browser()

        page = await self.browser.get("https://chat.deepseek.com/sign_up")
        await page.sleep(5)

        # Wait for page to load and WAF to be solved
        for i in range(max_wait // 3):
            await page.sleep(3)

            # Check if blocked by Cloudflare
            html = await page.get_content()
            if "ERROR" in html[:500] and "request could not be satisfied" in html[:500]:
                logger.error("Page blocked by Cloudflare WAF")
                return None

            # Check if Turnstile object is available
            has_turnstile = await page.evaluate(
                "typeof turnstile !== 'undefined'"
            )
            if not has_turnstile:
                # Maybe still loading, wait
                continue

            # Turnstile is available, render a widget and get token
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

    async def stop(self):
        if self.browser:
            await self.browser.stop()
            self.browser = None

    def get_token_sync(self, max_wait: int = 60) -> str | None:
        return asyncio.run(self.get_token(max_wait))
