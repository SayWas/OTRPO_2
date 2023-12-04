import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST_TEST")
DB_PORT = os.getenv("DB_PORT_TEST")
DB_NAME = os.getenv("DB_NAME_TEST")
DB_USER = os.getenv("DB_USER_TEST")
DB_PASSWORD = os.getenv("DB_PASSWORD_TEST")

DB_HOST_TEST = os.getenv("DB_HOST_TEST")
DB_PORT_TEST = os.getenv("DB_PORT_TEST")
DB_NAME_TEST = os.getenv("DB_NAME_TEST")
DB_USER_TEST = os.getenv("DB_USER_TEST")
DB_PASSWORD_TEST = os.getenv("DB_PASSWORD_TEST")

EMAIL_LOGIN = os.getenv("EMAIL_LOGIN", 'default_login')
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", 'default_password')

FTP_HOST = os.getenv("FTP_HOST", 'default_host')
FTP_PORT = int(os.getenv("FTP_PORT", '21'))

REDIS_HOST = os.getenv("REDIS_HOST", 'default_host')
REDIS_PORT = os.getenv("REDIS_PORT", '6379')
