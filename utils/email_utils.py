import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_ID, EMAIL_PASSWORD
from utils.logger import logger

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_username = EMAIL_ID
        self.smtp_password = EMAIL_PASSWORD
        self.from_email = EMAIL_ID

    async def send_mail(self, receiver: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Generic email sending function"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = receiver
            msg['Subject'] = subject

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Email send successfully to {receiver}")
            return True
        except Exception as e:
            logger.error(f"Email sending failed to {receiver}: {e}")
            return False