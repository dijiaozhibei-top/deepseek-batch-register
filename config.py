import os

# Gmail POP3 settings
GMAIL_ACCOUNT = os.getenv("GMAIL_ACCOUNT", "dijiaozhibei@gmail.com")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "pfca nrvg bqqb hthu")
POP3_SERVER = "pop.gmail.com"
POP3_PORT = 995

# DeepSeek settings
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://chat.deepseek.com")
# Set to "https://platform.deepseek.com" for API platform accounts

# Proxy (required for local testing in China)
PROXY = os.getenv("PROXY", "")

# Account settings
PASSWORD_LENGTH = 16
COUNT = int(os.getenv("REGISTER_COUNT", "3"))
START_INDEX = int(os.getenv("START_INDEX", "1"))

# Output file
ACCOUNTS_FILE = "accounts.csv"
