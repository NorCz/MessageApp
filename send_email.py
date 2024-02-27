import os
import smtplib
import ssl


def send_email(destination_email, code):
    send_generic_email(destination_email, f"Subject: Hi there\n\n Your code is {code}")


def send_generic_email(destination_email, contents):
    smtp_server = os.getenv('smtp_server')
    port = int(os.getenv('smtp_port'))  # For starttls
    sender_email = os.getenv('sender_email')
    password = os.getenv('password')
    context = ssl.create_default_context()
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo()  # Can be omitted
    server.starttls(context=context)  # Secure the connection
    server.ehlo()  # Can be omitted
    server.login(sender_email, password)
    server.sendmail(sender_email, destination_email, contents)