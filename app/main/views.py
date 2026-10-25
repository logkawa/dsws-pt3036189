from flask import render_template, session, redirect, url_for, current_app
from sqlalchemy import or_

from .. import db
from ..models import User, Role
from ..email import send_simple_message
from . import main
from .forms import NameForm


@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()

    if form.validate_on_submit():
        username = form.name.data.strip()
        email = form.email.data.strip().lower()

        # Verificar se o nome ou o e-mail já estão cadastrados
        user = User.query.filter(
            or_(
                User.username == username,
                User.email == email
            )
        ).first()

        if user:
            session['known'] = True
            session['name'] = user.username

            if user.username == username and user.email == email:
                session['email_status'] = (
                    'Este usuário já está cadastrado.'
                )
            elif user.username == username:
                session['email_status'] = (
                    'Este nome de usuário já está cadastrado.'
                )
            else:
                session['email_status'] = (
                    'Este e-mail já está cadastrado.'
                )

            return redirect(url_for('.index'))

        # Cadastrar o usuário no banco de dados
        try:
            default_role = Role.query.filter_by(name='User').first()

            if default_role is None:
                default_role = Role(name='User')
                db.session.add(default_role)
                db.session.flush()

            user = User(
                username=username,
                email=email,
                role=default_role
            )

            db.session.add(user)
            db.session.commit()

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                'Erro ao cadastrar usuário no banco de dados.'
            )

            session['email_status'] = (
                'Não foi possível concluir o cadastro.'
            )

            return redirect(url_for('.index'))

        session['known'] = False
        session['name'] = username

        # Enviar e-mail para o administrador
        admin_email = current_app.config.get('FLASKY_ADMIN')

        if admin_email:
            try:
                send_simple_message(
                    admin_email,
                    'Novo usuário cadastrado',
                    f'Um novo usuário foi cadastrado.\n\n'
                    f'Nome: {username}\n'
                    f'E-mail: {email}'
                )

                current_app.logger.info(
                    'Solicitação de envio ao administrador aceita.'
                )

            except Exception:
                current_app.logger.exception(
                    'Erro ao enviar e-mail ao administrador.'
                )

        else:
            current_app.logger.error(
                'FLASKY_ADMIN não está configurado.'
            )

        # Enviar e-mail para o usuário cadastrado
        try:
            send_simple_message(
                email,
                'Cadastro realizado com sucesso',
                f'Olá, {username}!\n\n'
                f'Seu cadastro foi realizado com sucesso.\n'
                f'Seja bem-vindo!'
            )

            current_app.logger.info(
                'Solicitação de envio ao usuário %s aceita.',
                email
            )

            session['email_status'] = (
                'Cadastro realizado! As solicitações de envio '
                'dos e-mails foram processadas.'
            )

        except Exception:
            current_app.logger.exception(
                'Erro ao enviar e-mail de confirmação para o usuário %s.',
                email
            )

            session['email_status'] = (
                'Usuário cadastrado, mas ocorreu um erro ao enviar '
                'o e-mail de confirmação. Consulte o log da aplicação.'
            )

        return redirect(url_for('.index'))

    # Listar os usuários cadastrados
    users = User.query.order_by(User.id.asc()).all()

    return render_template(
        'index.html',
        form=form,
        name=session.get('name'),
        known=session.get('known', False),
        email_status=session.pop('email_status', None),
        users=users
    )