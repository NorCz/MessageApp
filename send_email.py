import asyncio
import os
import ssl
import aiosmtplib
from email.message import EmailMessage


def send_email(destination_email, code):
    asyncio.run(send_generic_email(destination_email, "Hi there", f"Your code is {code}"))


async def send_generic_email(destination_email, subject, contents):
    smtp_server = os.getenv('smtp_server')
    port = int(os.getenv('smtp_port'))  # For starttls
    smtp_client = aiosmtplib.SMTP(hostname=os.getenv('smtp_server'), port=int(os.getenv('smtp_port')), tls_context=ssl.create_default_context())
    message = EmailMessage()
    message["From"] = os.getenv('sender_email')
    message["To"] = destination_email
    message["Subject"] = subject
    message.set_content(contents)
    await smtp_client.connect()
    await smtp_client.starttls()
    await smtp_client.login(os.getenv('sender_email'), os.getenv('password'))
    await smtp_client.send_message(message)
    await smtp_client.quit()
