import asyncio
import os
import ssl
import aiosmtplib
from email.message import EmailMessage
sem = asyncio.Semaphore(1)
from dotenv import load_dotenv


load_dotenv('/app/backend/.env', verbose=True, override=True)

def send_email(destination_email, code):
    asyncio.run(send_generic_email(destination_email, "Hi there", f"Your code is {code}"))


async def send_generic_email(destination_email, subject, contents):
    async with sem:
        try:
            smtp_client = aiosmtplib.SMTP(hostname=os.getenv('smtp_server'), port=int(os.getenv('smtp_port')), tls_context=ssl.create_default_context(), use_tls=True) # Port 465 for ssl/tls encrypted
            message = EmailMessage()
            message["From"] = os.getenv('sender_email')
            message["To"] = destination_email
            message["Subject"] = subject
            message.set_content(contents)
            await smtp_client.connect()
            await smtp_client.login(os.getenv('sender_email'), os.getenv('password'))
            await smtp_client.send_message(message)
            await smtp_client.quit()
        except aiosmtplib.errors.SMTPException as e:
            print(f"[MAIL] Error sending message to {destination_email} ({type(e)}: {e.message}).")
        except Exception as e:
            print(f"[MAIL] Non-SMPT error sending message to {destination_email}  ({type(e)}).")
