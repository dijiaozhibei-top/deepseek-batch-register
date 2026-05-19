import json
import logging
import os
import random
import string
import time

from curl_cffi import requests

logger = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self, base_url: str = "https://chat.deepseek.com", proxy: str = ""):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.impersonate = "chrome120"

        if proxy:
            self.session.proxies = {
                "http": proxy,
                "https": proxy,
            }
            logger.info(f"使用代理: {proxy}")

        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })

    def _generate_password(self, length: int = 16) -> str:
        chars = string.ascii_letters + string.digits
        password = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
        ]
        password += [random.choice(chars) for _ in range(length - len(password))]
        random.shuffle(password)
        return "".join(password)

    def send_code(self, email: str) -> bool:
        url = f"{self.base_url}/api/v0/users/send-code"
        payload = {"email": email}

        try:
            resp = self.session.post(url, json=payload)
            if resp.status_code in (200, 201):
                data = resp.json()
                if data.get("code") == 0 or data.get("success") is not False:
                    logger.info(f"[{email}] 验证码发送成功")
                    return True
                else:
                    logger.warning(f"[{email}] 发送验证码返回异常: {data}")
                    return False
            else:
                logger.error(f"[{email}] 发送验证码失败 HTTP {resp.status_code}: {resp.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"[{email}] 发送验证码请求异常: {e}")
            return False

    def register(self, email: str, code: str, password: str) -> dict | None:
        url = f"{self.base_url}/api/v0/users/register"
        payload = {
            "email": email,
            "password": password,
            "code": code,
        }

        try:
            resp = self.session.post(url, json=payload)
            if resp.status_code in (200, 201):
                data = resp.json()
                if data.get("code") == 0:
                    token = (
                        data.get("data", {}).get("biz_data", {}).get("user", {}).get("token")
                        or data.get("data", {}).get("token")
                    )
                    logger.info(f"[{email}] 注册成功")
                    return {
                        "email": email,
                        "password": password,
                        "token": token,
                        "raw_response": data,
                    }
                else:
                    logger.warning(f"[{email}] 注册返回异常: {data}")
                    return None
            else:
                logger.error(f"[{email}] 注册失败 HTTP {resp.status_code}: {resp.text[:300]}")
                return None
        except Exception as e:
            logger.error(f"[{email}] 注册请求异常: {e}")
            return None

    def register_account(self, email: str, password_length: int = 16,
                         max_code_retries: int = 15, code_interval: int = 10) -> dict | None:
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
        if result:
            result["password"] = password
            return result

        return None
