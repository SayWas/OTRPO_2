import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

EMAIL_LOGIN = os.getenv("EMAIL_LOGIN", 'default_login')
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", 'default_password')

FTP_HOST = os.getenv("FTP_HOST", 'default_host')
FTP_PORT = int(os.getenv("FTP_PORT", '21'))

REDIS_HOST = os.getenv("REDIS_HOST", 'default_host')
REDIS_PORT = os.getenv("REDIS_PORT", '6379')

AUTH_SECRET = os.getenv("AUTH_SECRET")
MANAGER_SECRET = os.getenv("MANAGER_SECRET")
RESET_SECRET = os.getenv("RESET_SECRET")
VERIFICATION_SECRET = os.getenv("VERIFICATION_SECRET")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
STATE_SECRET = os.getenv("STATE_SECRET")
