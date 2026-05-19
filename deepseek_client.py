import json
import logging
import random
import string
import urllib.request
import uuid

import ssl

logger = logging.getLogger(__name__)


class DeepSeekAPIClient:
    def __init__(self, base_url: str = "https://chat.deepseek.com", proxy: str = ""):
        self.base_url = base_url.rstrip("/")
        self.proxy = proxy

    def _request(self, method: str, path: str, payload: dict) -> tuple[int, str]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url, data=data, method=method,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/sign_up",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
        )

        if self.proxy:
            proxy_handler = urllib.request.ProxyHandler({"http": self.proxy, "https": self.proxy})
            opener = urllib.request.build_opener(proxy_handler)
            resp = opener.open(req, timeout=30)
        else:
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, timeout=30, context=ctx)

        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body

    def send_code(self, email: str) -> bool:
        payload_configs = [
            {"email": email, "scenario": "signUp"},
            {"email": email, "scenario": "register"},
            {"email": email, "scenario": "sign_up"},
            {"email": email},
        ]

        for payload in payload_configs:
            try:
                status, body = self._request("POST", "/api/v0/users/create_email_verification_code", payload)
                logger.info(f"[{email}] 尝试 {payload} -> status={status}, body={body[:300]}")

                if status == 200:
                    data = json.loads(body)
                    if data.get("code") == 0:
                        logger.info(f"[{email}] 验证码发送成功")
                        return True
                elif status == 422:
                    continue
                else:
                    logger.error(f"[{email}] HTTP {status}: {body[:300]}")
                    return False
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                logger.warning(f"[{email}] 尝试 {payload} -> HTTP {e.code}: {body[:200]}")
                continue
            except Exception as e:
                logger.warning(f"[{email}] 尝试 {payload} -> 异常: {e}")
                continue

        logger.error(f"[{email}] 所有payload配置均失败")
        return False

    def register(self, email: str, code: str, password: str) -> dict | None:
        payload = {
            "email": email,
            "password": password,
            "code": code,
        }

        try:
            status, body = self._request("POST", "/api/v0/users/register", payload)
            logger.debug(f"register: status={status}, body={body[:500]}")

            if status == 200:
                data = json.loads(body)
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
                logger.error(f"[{email}] HTTP {status}: {body[:300]}")
                return None

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error(f"[{email}] HTTP {e.code}: {body[:300]}")
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
