import smtplib
import ssl


def send_email(destination_email, code):
    smtp_server = "smtp.gmail.com"
    port = 587  # For starttls
    sender_email = "messageappforcompetition@gmail.com"
    password = "dapp cjlz wzru soyg"
    context = ssl.create_default_context()
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo()  # Can be omitted
    server.starttls(context=context)  # Secure the connection
    server.ehlo()  # Can be omitted
    server.login(sender_email, password)
    message = f"Subject: Hi there\n\n Your code is {code}"
    server.sendmail(sender_email, destination_email, message)
