from flask import render_template
from flask_mail import Message
from application import mail, app
from threading import Thread


def send_async_email(app, msg):
    # context of the app must be stated manually
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject=subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(subject='[RecipeShare] Reset your Password', sender=app.config['ADMINS'][0], recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token))
