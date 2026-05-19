import poplib
import email
from email import message as email_message
import email.message
import re
import time
import logging
from email.header import decode_header

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self, account: str, password: str, server: str = "pop.gmail.com", port: int = 995):
        self.account = account
        self.password = password
        self.server = server
        self.port = port

    def _decode_str(self, s: str) -> str:
        parts = decode_header(s)
        result = []
        for part, charset in parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    def get_verification_code(self, alias_email: str, max_retries: int = 12, retry_interval: int = 10) -> str | None:
        for attempt in range(1, max_retries + 1):
            logger.info(f"[{alias_email}] 等待验证码邮件... 第 {attempt}/{max_retries} 次检查")
            try:
                code = self._fetch_code(alias_email)
                if code:
                    logger.info(f"[{alias_email}] 成功获取验证码: {code}")
                    return code
            except Exception as e:
                logger.warning(f"[{alias_email}] 检查邮件失败: {e}")

            if attempt < max_retries:
                time.sleep(retry_interval)

        logger.error(f"[{alias_email}] 超过最大重试次数，未能获取验证码")
        return None

    def _fetch_code(self, alias_email: str) -> str | None:
        conn = poplib.POP3_SSL(self.server, self.port, timeout=30)
        try:
            conn.user(self.account)
            conn.pass_(self.password)

            msg_count = len(conn.list()[1])
            if msg_count == 0:
                return None

            for i in range(msg_count, max(0, msg_count - 5), -1):
                raw_lines = conn.retr(i)[1]
                raw_message = b"\r\n".join(raw_lines)
                msg = email.message_from_bytes(raw_message)

                subject = self._decode_str(msg.get("Subject", ""))
                sender = self._decode_str(msg.get("From", ""))
                logger.debug(f"  邮件 [{i}]: Subject={subject}, From={sender}")

                if "deepseek" not in subject.lower() and "deepseek" not in sender.lower():
                    continue

                body = self._get_email_body(msg)
                if not body:
                    continue

                code = self._extract_code(body)
                if code:
                    return code
        finally:
            conn.quit()

        return None

    def _get_email_body(self, msg: email.message.Message) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        return part.get_payload(decode=True).decode(charset, errors="replace")
                    except Exception:
                        continue
                elif content_type == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        return part.get_payload(decode=True).decode(charset, errors="replace")
                    except Exception:
                        continue
        else:
            charset = msg.get_content_charset() or "utf-8"
            try:
                return msg.get_payload(decode=True).decode(charset, errors="replace")
            except Exception:
                return ""
        return ""

    def _extract_code(self, body: str) -> str | None:
        patterns = [
            r"verification\s*code[:\s]*(\d{6})",
            r"验证码[：:\s]*(\d{6})",
            r"code[:\s]*(\d{6})",
            r"(\d{6})\s*(?:is your|验证码)",
        ]
        for pattern in patterns:
            m = re.search(pattern, body, re.IGNORECASE)
            if m:
                return m.group(1)

        nums = re.findall(r"\b(\d{6})\b", body)
        if nums:
            return nums[-1]

        return None

    def clean_messages(self):
        try:
            conn = poplib.POP3_SSL(self.server, self.port, timeout=30)
            try:
                conn.user(self.account)
                conn.pass_(self.password)
                msg_count = len(conn.list()[1])
                for i in range(msg_count, 0, -1):
                    raw_lines = conn.retr(i)[1]
                    raw_message = b"\r\n".join(raw_lines)
                    msg = email.message_from_bytes(raw_message)
                    subject = self._decode_str(msg.get("Subject", ""))
                    if "deepseek" in subject.lower():
                        conn.dele(i)
                        logger.info(f"  已删除邮件 [{i}]: {subject}")
            finally:
                conn.quit()
        except Exception as e:
            logger.warning(f"清理邮件失败: {e}")
