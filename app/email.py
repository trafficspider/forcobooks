from flask_mail import Message
from flask import current_app
from app import mail
import logging

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    try:
        mail.send(msg)
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        logging.error(f"MAIL_SERVER: {current_app.config['MAIL_SERVER']}")
        logging.error(f"MAIL_PORT: {current_app.config['MAIL_PORT']}")
        logging.error(f"MAIL_USE_TLS: {current_app.config['MAIL_USE_TLS']}")
        logging.error(f"MAIL_USERNAME: {current_app.config['MAIL_USERNAME']}")
        logging.error(f"MAIL_DEFAULT_SENDER: {current_app.config['MAIL_DEFAULT_SENDER']}")
        raise
