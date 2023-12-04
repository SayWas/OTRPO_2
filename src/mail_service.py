import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydantic import EmailStr

from .config import EMAIL_LOGIN, EMAIL_PASSWORD
from .schemas import LogSchema


def send_logs_mail(email: EmailStr, log: LogSchema):
    print(EMAIL_PASSWORD, EMAIL_LOGIN)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Битва покемонов"
    msg['From'] = EMAIL_LOGIN
    msg['To'] = email

    html = f"""\
    <html>
      <head></head>
      <body>
        <p>
            Здравствуйте!<br>
            Битва прошла следующим образом: Победитель - {log.winner_id}, Проигравший - {log.loser_id}, Всего раундов - {log.total_rounds}
        </p>
      </body>
    </html>
    """

    part2 = MIMEText(html, 'html')

    msg.attach(part2)

    server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    server.login(EMAIL_LOGIN, EMAIL_PASSWORD)
    server.sendmail(EMAIL_LOGIN, email, msg.as_string())
    server.quit()


def send_otp_mail(email: EmailStr, otp: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Ваш одноразовый код"
    msg['From'] = EMAIL_LOGIN
    msg['To'] = email

    html = f"""\
    <html>
      <head></head>
      <body>
        <p>
            Здравствуйте!<br>
            Ваш одноразовый код для входа: <b>{otp}</b>
        </p>
      </body>
    </html>
    """

    part2 = MIMEText(html, 'html')

    msg.attach(part2)

    server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    server.login(EMAIL_LOGIN, EMAIL_PASSWORD)
    server.sendmail(EMAIL_LOGIN, email, msg.as_string())
    server.quit()


def send_reset_password_mail(email: EmailStr, token: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Сброс пароля"
    msg['From'] = EMAIL_LOGIN
    msg['To'] = email

    html = f"""\
    <html>
      <head></head>
      <body>
        <p>
            Здравствуйте!<br>
            Для сброса пароля перейдите по ссылке: <a href="http://localhost:5173/reset-password?token={token}">http://localhost:5173/reset-password?token={token}</a>
        </p>
      </body>
    </html>
    """

    part2 = MIMEText(html, 'html')

    msg.attach(part2)

    server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    server.login(EMAIL_LOGIN, EMAIL_PASSWORD)
    server.sendmail(EMAIL_LOGIN, email, msg.as_string())
    server.quit()
