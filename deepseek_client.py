import json
import logging
import random
import string
import uuid

from curl_cffi import requests

logger = logging.getLogger(__name__)


class DeepSeekAPIClient:
    def __init__(self, base_url: str = "https://chat.deepseek.com", proxy: str = ""):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session(impersonate="chrome131")

        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
            logger.info(f"使用代理: {proxy}")

        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/sign_up",
        })

    def send_code(self, email: str) -> bool:
        url = f"{self.base_url}/api/v0/users/create_email_verification_code"
        payload = {
            "email": email,
            "turnstile_token": "dummy",
            "device_id": str(uuid.uuid4()),
            "scenario": "signUp",
            "locale": "en_US",
        }

        try:
            resp = self.session.post(url, json=payload, timeout=30)
            logger.debug(f"send-code: status={resp.status_code}, body={resp.text[:500]}")

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    logger.info(f"[{email}] 验证码发送成功")
                    return True
                else:
                    logger.warning(f"[{email}] 返回: {data}")
                    return False
            elif resp.status_code == 422:
                logger.error(f"[{email}] 需要Turnstile验证: {resp.text[:300]}")
                return False
            else:
                logger.error(f"[{email}] HTTP {resp.status_code}: {resp.text[:300]}")
                return False

        except Exception as e:
            logger.error(f"[{email}] 异常: {e}")
            return False

    def register(self, email: str, code: str, password: str) -> dict | None:
        url = f"{self.base_url}/api/v0/users/register"
        payload = {
            "email": email,
            "password": password,
            "code": code,
        }

        try:
            resp = self.session.post(url, json=payload, timeout=30)
            logger.debug(f"register: status={resp.status_code}, body={resp.text[:500]}")

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    token = (
                        data.get("data", {}).get("biz_data", {}).get("user", {}).get("token")
                        or data.get("data", {}).get("token", "")
                    )
                    logger.info(f"[{email}] 注册成功")
                    return {"email": email, "password": password, "token": token}
                else:
                    logger.warning(f"[{email}] 返回: {data}")
                    return None
            else:
                logger.error(f"[{email}] HTTP {resp.status_code}: {resp.text[:300]}")
                return None

        except Exception as e:
            logger.error(f"[{email}] 异常: {e}")
            return None

    def _generate_password(self, length: int = 16) -> str:
        chars = string.ascii_letters + string.digits
        pw = [random.choice(string.ascii_uppercase), random.choice(string.ascii_lowercase), random.choice(string.digits)]
        pw += [random.choice(chars) for _ in range(length - len(pw))]
        random.shuffle(pw)
        return "".join(pw)

    def register_account(self, email: str, password_length: int = 16,
                         max_code_retries: int = 12, code_interval: int = 10) -> dict | None:
        password = self._generate_password(password_length)
        logger.info(f"[{email}] 开始注册，密码: {password}")

        success = self.send_code(email)
        if not success:
            logger.error(f"[{email}] 发送验证码失败，跳过")
            return None

        from email_client import EmailClient
        import config
        ec = EmailClient(config.GMAIL_ACCOUNT, config.GMAIL_PASSWORD)
        code = ec.get_verification_code(email, max_retries=max_code_retries, retry_interval=code_interval)
        if not code:
            logger.error(f"[{email}] 获取验证码失败，跳过")
            return None

        result = self.register(email, code, password)
        return result
