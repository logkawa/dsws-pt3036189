from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail

import requests
from datetime import datetime

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


def send_simple_message(to, subject, newUser):
    app = current_app._get_current_object()

    try:
        resposta = requests.post(
            app.config['API_URL'],
            auth=('api', app.config['API_KEY']),
            data={
                'from': app.config['API_FROM'],
                'to': to,
                'subject': (
                    app.config['FLASKY_MAIL_SUBJECT_PREFIX']
                    + ' ' + subject
                ),
                'text': 'Novo usuário cadastrado: ' + newUser
            },
            timeout=15
        )

        print(
            'Resposta do Mailgun:',
            resposta.status_code,
            flush=True
        )

        return resposta

    except requests.RequestException as erro:
        print('Erro ao enviar e-mail:', erro, flush=True)
        return None
