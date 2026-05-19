import csv
import logging
import os
import sys
import time
import asyncio

import config
from playwright_register import DeepSeekPlaywrightRegister
from email_client import EmailClient

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/register.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def save_account(account: dict):
    file_exists = os.path.isfile(config.ACCOUNTS_FILE)
    with open(config.ACCOUNTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["email", "password", "token"])
        writer.writerow([
            account.get("email", ""),
            account.get("password", ""),
            account.get("token", ""),
        ])
    logger.info(f"账号已保存: {account['email']}")


def build_alias_email(base_account: str, index: int) -> str:
    name, domain = base_account.split("@")
    return f"{name}+{index}@{domain}"


async def main_async():
    logger.info("=" * 50)
    logger.info("DeepSeek 批量注册工具启动 (Playwright)")
    logger.info(f"目标邮箱: {config.GMAIL_ACCOUNT}")
    logger.info(f"注册数量: {config.COUNT}")
    logger.info(f"起始索引: {config.START_INDEX}")
    logger.info(f"目标站点: {config.DEEPSEEK_BASE_URL}")
    if config.PROXY:
        logger.info(f"代理: {config.PROXY}")
    logger.info("=" * 50)

    success_count = 0
    fail_count = 0

    for i in range(config.START_INDEX, config.START_INDEX + config.COUNT):
        alias_email = build_alias_email(config.GMAIL_ACCOUNT, i)
        logger.info(f"\n--- 正在注册第 {i} 个账号: {alias_email} ---")

        try:
            client = DeepSeekPlaywrightRegister(
                base_url=config.DEEPSEEK_BASE_URL,
                proxy=config.PROXY,
                headless=True,
            )

            result = await client.register_account(
                email=alias_email,
                password_length=config.PASSWORD_LENGTH,
                code_retries=12,
                code_interval=10,
            )

            if result:
                save_account(result)
                success_count += 1
            else:
                fail_count += 1

        except Exception as e:
            logger.exception(f"[{alias_email}] 注册过程发生异常: {e}")
            fail_count += 1

        if i < config.START_INDEX + config.COUNT - 1:
            wait_time = 30
            logger.info(f"等待 {wait_time} 秒后进行下一个注册...")
            time.sleep(wait_time)

    logger.info("\n" + "=" * 50)
    logger.info("注册完成！")
    logger.info(f"成功: {success_count}, 失败: {fail_count}")
    logger.info(f"账号已保存至: {config.ACCOUNTS_FILE}")
    logger.info("=" * 50)

    return 0 if fail_count == 0 else 1


def main():
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
