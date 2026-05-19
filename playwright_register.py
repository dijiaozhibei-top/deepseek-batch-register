import asyncio
import json
import logging
import os
import random
import string
import time

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class DeepSeekPlaywrightRegister:
    def __init__(self, base_url: str = "https://chat.deepseek.com", proxy: str = "", headless: bool = True):
        self.base_url = base_url.rstrip("/")
        self.proxy = proxy
        self.headless = headless

    def _generate_password(self, length: int = 16) -> str:
        chars = string.ascii_letters + string.digits
        pw = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
        ]
        pw += [random.choice(chars) for _ in range(length - len(pw))]
        random.shuffle(pw)
        return "".join(pw)

    async def register_account(self, email: str, password_length: int = 16,
                               code_retries: int = 12, code_interval: int = 10) -> dict | None:
        password = self._generate_password(password_length)
        logger.info(f"[{email}] 开始注册，密码: {password}")

        try:
            result = await self._do_register(email, password, code_retries, code_interval)
            if result:
                result["password"] = password
                logger.info(f"[{email}] 注册成功")
                return result
            return None
        except Exception as e:
            logger.exception(f"[{email}] 注册异常: {e}")
            return None

    async def _do_register(self, email: str, password: str,
                           code_retries: int, code_interval: int) -> dict | None:
        async with async_playwright() as p:
            browser_args = {
                "headless": self.headless,
                "args": [
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            }
            if self.proxy:
                browser_args["proxy"] = {"server": self.proxy}

            browser = await p.chromium.launch(**browser_args)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )

            page = await context.new_page()

            # Intercept API responses
            api_results = {}

            async def on_response(response):
                url = response.url
                if "create_email_verification_code" in url:
                    try:
                        data = await response.json()
                        api_results["send_code"] = data
                        logger.info(f"[{email}] send-code API响应: {json.dumps(data, ensure_ascii=False)[:200]}")
                    except Exception:
                        logger.warning(f"[{email}] send-code API响应非JSON")

                elif "/users/register" in url or "/v0/users/register" in url:
                    try:
                        data = await response.json()
                        api_results["register"] = data
                        logger.info(f"[{email}] register API响应: {json.dumps(data, ensure_ascii=False)[:200]}")
                    except Exception:
                        logger.warning(f"[{email}] register API响应非JSON")

            page.on("response", on_response)

            try:
                sign_up_url = f"{self.base_url}/sign_up"
                logger.info(f"[{email}] 打开页面: {sign_up_url}")
                await page.goto(sign_up_url, timeout=60000, wait_until="networkidle")
                await asyncio.sleep(5)

                current_url = page.url
                logger.info(f"[{email}] 当前URL: {current_url}")

                page_title = await page.title()
                page_html = await page.content()
                logger.info(f"[{email}] 页面标题: {page_title}")
                logger.debug(f"[{email}] 页面HTML (前2000字): {page_html[:2000]}")

                if "sign_up" not in current_url and "auth" not in current_url and "login" not in current_url:
                    logger.info(f"[{email}] 页面被重定向到: {current_url}，尝试直接导航到sign_up")
                    await page.goto(sign_up_url, timeout=30000, wait_until="networkidle")
                    await asyncio.sleep(3)

                email_input = await page.wait_for_selector(
                    "input[type='email'], input[placeholder*='mail'], input[name='email'], input:not([type='hidden'])",
                    timeout=30000
                )
                if not email_input:
                    inputs = await page.query_selector_all("input")
                    logger.info(f"[{email}] 页面共 {len(inputs)} 个input元素")
                    for idx, inp in enumerate(inputs):
                        html = await page.evaluate("el => el.outerHTML", inp)
                        logger.info(f"  input[{idx}]: {html[:200]}")
                    for inp in inputs:
                        placeholder = await inp.get_attribute("placeholder") or ""
                        input_type = await inp.get_attribute("type") or ""
                        if "mail" in placeholder.lower() or "email" in placeholder.lower() or input_type == "email":
                            email_input = inp
                            break

                if not email_input:
                    raise Exception("找不到邮箱输入框")

                await email_input.click()
                await email_input.fill(email)
                logger.info(f"[{email}] 已填入邮箱")

                await asyncio.sleep(2)

                send_btn = await page.query_selector("button:has-text('Send'), button:has-text('发送'), button:has-text('Get Code'), button:has-text('获取')")
                if not send_btn:
                    buttons = await page.query_selector_all("button")
                    for btn in buttons:
                        text = await btn.inner_text()
                        if text.strip():
                            send_btn = btn
                            break

                if not send_btn:
                    raise Exception("找不到发送按钮")

                await send_btn.click()
                logger.info(f"[{email}] 已点击发送验证码")

                await asyncio.sleep(5)

                if "send_code" in api_results:
                    send_data = api_results["send_code"]
                    if send_data.get("code") == 0:
                        logger.info(f"[{email}] 验证码发送成功")
                    else:
                        logger.warning(f"[{email}] 发送验证码API返回: {send_data}")
                else:
                    logger.warning(f"[{email}] 未捕获到send-code API响应，等待中...")
                    for i in range(10):
                        await asyncio.sleep(2)
                        if "send_code" in api_results:
                            logger.info(f"[{email}] 捕获到send-code API响应")
                            break

                from email_client import EmailClient
                import config

                ec = EmailClient(config.GMAIL_ACCOUNT, config.GMAIL_PASSWORD)
                code = None
                for attempt in range(1, code_retries + 1):
                    logger.info(f"[{email}] 检查验证码邮件... 第{attempt}/{code_retries}次")
                    try:
                        code = ec._fetch_code(email)
                        if code:
                            logger.info(f"[{email}] 获取到验证码: {code}")
                            break
                    except Exception as e:
                        logger.warning(f"检查邮件异常: {e}")
                    if attempt < code_retries:
                        await asyncio.sleep(code_interval)

                if not code:
                    logger.error(f"[{email}] 获取验证码失败")
                    return None

                code_inputs = await page.query_selector_all("input[type='text'], input[type='tel']")
                code_filled = False
                for inp in code_inputs:
                    max_len = await inp.get_attribute("maxlength")
                    if max_len == "6" or max_len == "1":
                        await inp.click()
                        await inp.fill(code)
                        code_filled = True
                        logger.info(f"[{email}] 已填入验证码")
                        break

                if not code_filled:
                    logger.info(f"[{email}] 尝试在其他输入框填入验证码")
                    all_inputs = await page.query_selector_all("input:not([type='email']):not([type='hidden'])")
                    for inp in all_inputs:
                        try:
                            await inp.click()
                            await inp.fill(code)
                            code_filled = True
                            break
                        except Exception:
                            continue

                await asyncio.sleep(2)

                password_input = await page.query_selector("input[type='password']")
                if password_input:
                    await password_input.click()
                    await password_input.fill(password)
                    logger.info(f"[{email}] 已填入密码")

                await asyncio.sleep(1)

                submit_btn = await page.query_selector(
                    "button:has-text('Register'), button:has-text('Sign Up'), "
                    "button:has-text('注册'), button:has-text('Sign'), "
                    "button:has-text('Continue'), button[type='submit']"
                )
                if submit_btn:
                    await submit_btn.click()
                    logger.info(f"[{email}] 已提交注册")
                else:
                    logger.warning(f"[{email}] 找不到提交按钮，尝试回车")
                    await page.keyboard.press("Enter")

                await asyncio.sleep(5)

                if "register" in api_results:
                    reg_data = api_results["register"]
                    if reg_data.get("code") == 0:
                        token = (
                            reg_data.get("data", {}).get("biz_data", {}).get("user", {}).get("token")
                            or reg_data.get("data", {}).get("token")
                        )
                        return {"email": email, "token": token or ""}

                    logger.warning(f"[{email}] 注册API返回: {reg_data}")
                    return None

                page_content = await page.content()
                if "success" in page_content.lower() or "welcome" in page_content.lower():
                    logger.info(f"[{email}] 页面内容提示注册成功")
                    return {"email": email, "token": ""}

                logger.warning(f"[{email}] 未捕获到register API响应，检测页面URL: {page.url}")
                return None

            finally:
                await browser.close()
