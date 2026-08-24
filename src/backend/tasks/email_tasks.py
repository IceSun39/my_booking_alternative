import smtplib
import ssl
import os
import socket
import logging

from dotenv import load_dotenv
from email.message import EmailMessage
from src.backend.core.celery_app import celery

load_dotenv()
logger = logging.getLogger(__name__)

port = 465
smtp_server = "smtp.gmail.com"
sender_email = "vlad.dev.3241@gmail.com"
password = os.getenv("EMAIL_PASSWORD")


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, subject, message, message_html, from_email, to_email, **kwargs):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    msg.set_content(message)
    if message_html:
        msg.add_alternative(message_html, subtype="html")

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.send_message(msg)

        logger.info(f"Email successfully send to {to_email}")

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication error SMTP. Check EMAIL_PASSWORD: {e}")
        raise e

    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipients address refused: ({to_email}): {e}")
        raise e

    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, socket.error, TimeoutError) as e:
        logger.warning(f"Connection error SMTP. Retry... Details: {e}")
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"Unexpected error while sending to {to_email}: {e}", exc_info=True)
        raise e