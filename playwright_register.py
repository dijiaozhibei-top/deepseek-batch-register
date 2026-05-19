import asyncio
import json
import logging
import random
import string

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

            sign_up_url = f"{self.base_url}/sign_up"
            logger.info(f"[{email}] 打开页面: {sign_up_url}")
            await page.goto(sign_up_url, timeout=60000, wait_until="load")
            await asyncio.sleep(5)

            current_url = page.url
            page_title = await page.title()
            logger.info(f"[{email}] URL: {current_url}, 标题: {page_title}")

            all_inputs = await page.query_selector_all("input")
            logger.info(f"[{email}] 页面共 {len(all_inputs)} 个input元素")
            for idx, inp in enumerate(all_inputs):
                try:
                    html = await page.evaluate("el => el.outerHTML", inp)
                    logger.info(f"  input[{idx}]: {html[:200]}")
                except Exception:
                    pass

            all_buttons = await page.query_selector_all("button")
            logger.info(f"[{email}] 页面共 {len(all_buttons)} 个button元素")
            for btn in all_buttons:
                try:
                    text = await btn.text_content()
                    if text and text.strip():
                        logger.info(f"  button: {text.strip()[:60]}")
                except Exception:
                    pass

            if "sign_up" not in current_url and "auth" not in current_url and "login" not in current_url:
                logger.warning(f"[{email}] 页面不在注册页 (URL: {current_url})，可能IP受限")
                return None

            identifier_input = None
            for inp in all_inputs:
                try:
                    t = await inp.get_attribute("type") or ""
                    p_val = await inp.get_attribute("placeholder") or ""
                    if t in ("email", "tel") or "mail" in p_val.lower() or "phone" in p_val.lower() or "手机" in p_val:
                        identifier_input = inp
                        break
                except Exception:
                    continue

            if not identifier_input and all_inputs:
                identifier_input = all_inputs[0]

            if not identifier_input:
                raise Exception("找不到邮箱/手机输入框")

            await identifier_input.click()
            await identifier_input.fill(email)
            logger.info(f"[{email}] 已填入标识")

            await asyncio.sleep(2)

            send_btn = None
            for btn in all_buttons:
                try:
                    text = await btn.text_content()
                    if text and ("获取" in text or "Send" in text or "Code" in text or "发送" in text):
                        send_btn = btn
                        break
                except Exception:
                    continue
            if not send_btn and all_buttons:
                for btn in all_buttons:
                    try:
                        text = await btn.text_content()
                        if text and text.strip():
                            send_btn = btn
                            break
                    except Exception:
                        continue

            if not send_btn:
                raise Exception("找不到发送验证码按钮")

            async def on_response(response):
                url = response.url
                if "create_email_verification_code" in url or "create_sms_verification_code" in url:
                    try:
                        data = await response.json()
                        logger.info(f"[{email}] 发送验证码响应: {json.dumps(data, ensure_ascii=False)[:200]}")
                    except Exception:
                        pass
                elif "/users/register" in url or "/v0/users/register" in url:
                    try:
                        data = await response.json()
                        logger.info(f"[{email}] 注册响应: {json.dumps(data, ensure_ascii=False)[:200]}")
                        self._register_result = data
                    except Exception:
                        pass

            page.on("response", on_response)

            await send_btn.click()
            logger.info(f"[{email}] 已点击发送验证码")
            await asyncio.sleep(5)

            from email_client import EmailClient
            import config

            ec = EmailClient(config.GMAIL_ACCOUNT, config.GMAIL_PASSWORD)
            code = None
            for attempt in range(1, code_retries + 1):
                logger.info(f"[{email}] 检查验证码... 第{attempt}/{code_retries}次")
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

            for inp in all_inputs:
                try:
                    max_len = await inp.get_attribute("maxlength") or ""
                    if max_len in ("6", "1"):
                        await inp.click()
                        await inp.fill(code)
                        logger.info(f"[{email}] 已填入验证码")
                        break
                except Exception:
                    continue

            await asyncio.sleep(2)

            pw_inputs = []
            for inp in all_inputs:
                try:
                    t = await inp.get_attribute("type") or ""
                    if t == "password":
                        pw_inputs.append(inp)
                except Exception:
                    continue

            if pw_inputs:
                await pw_inputs[0].click()
                await pw_inputs[0].fill(password)
                logger.info(f"[{email}] 已填入密码")
                if len(pw_inputs) > 1:
                    await pw_inputs[1].click()
                    await pw_inputs[1].fill(password)
                    logger.info(f"[{email}] 已填入确认密码")

            await asyncio.sleep(1)

            submit_btn = None
            for btn in all_buttons:
                try:
                    text = await btn.text_content()
                    if text and ("注册" in text or "Register" in text or "Sign" in text or "submit" in text.lower()):
                        submit_btn = btn
                        break
                except Exception:
                    continue

            if submit_btn:
                await submit_btn.click()
                logger.info(f"[{email}] 已点击提交")
            else:
                logger.warning(f"[{email}] 未找到提交按钮")
                return None

            await asyncio.sleep(5)

            reg_data = getattr(self, "_register_result", None)
            if reg_data:
                if reg_data.get("code") == 0:
                    token = (
                        reg_data.get("data", {}).get("biz_data", {}).get("user", {}).get("token")
                        or reg_data.get("data", {}).get("token", "")
                    )
                    return {"email": email, "token": token}
                logger.warning(f"[{email}] 注册失败: {reg_data}")
                return None

            final_url = page.url
            if "login" in final_url or "chat" in final_url:
                logger.info(f"[{email}] 注册成功，跳转至: {final_url}")
                return {"email": email, "token": ""}

            logger.warning(f"[{email}] 注册结果未知，URL: {final_url}")
            return None
