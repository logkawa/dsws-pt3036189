from flask import (
    render_template,
    session,
    redirect,
    url_for,
    current_app
)

from sqlalchemy import or_

from .. import db
from ..models import User, Role
from ..email import send_simple_message
from . import main
from .forms import NameForm, EditUserForm, DeleteUserForm


@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    delete_form = DeleteUserForm()

    # Cadastro de usuário
    if form.validate_on_submit():
        username = form.name.data.strip()
        email = form.email.data.strip().lower()

        existing_user = User.query.filter(
            or_(
                User.username == username,
                User.email == email
            )
        ).first()

        if existing_user:
            session['known'] = True
            session['name'] = existing_user.username
            session['email_status'] = (
                'Este nome de usuário ou e-mail já está cadastrado.'
            )
            return redirect(url_for('.index'))

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

            session['known'] = False
            session['name'] = username

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                'Erro ao cadastrar usuário.'
            )

            session['email_status'] = (
                'Não foi possível cadastrar o usuário.'
            )

            return redirect(url_for('.index'))

        # Notificação ao administrador
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

            except Exception:
                current_app.logger.exception(
                    'Erro ao enviar e-mail ao administrador.'
                )

        # E-mail de confirmação ao usuário
        try:
            send_simple_message(
                email,
                'Cadastro realizado com sucesso',
                f'Olá, {username}!\n\n'
                'Seu cadastro foi realizado com sucesso.\n'
                'Seja bem-vindo!'
            )

            session['email_status'] = (
                'Cadastro realizado! O envio do e-mail de confirmação '
                'foi solicitado.'
            )

        except Exception:
            current_app.logger.exception(
                'Erro ao enviar e-mail ao usuário.'
            )

            session['email_status'] = (
                'Usuário cadastrado, mas houve um erro ao enviar '
                'o e-mail de confirmação.'
            )

        return redirect(url_for('.index'))

    # Lista os usuários
    users = User.query.order_by(User.id.asc()).all()

    # Cria um formulário de edição para cada usuário.
    # O nome começa vazio para exibir o nome atual como placeholder.
    roles = Role.query.order_by(Role.name.asc()).all()
    edit_forms = {}

    for user in users:
        edit_form = EditUserForm()

        edit_form.username.data = user.username
        edit_form.email.data = user.email
        edit_form.role_id.data = user.role_id

        edit_form.role_id.choices = [
            (role.id, role.name)
            for role in roles
        ]

        edit_forms[user.id] = edit_form

    return render_template(
        'index.html',
        form=form,
        delete_form=delete_form,
        edit_forms=edit_forms,
        users=users,
        name=session.get('name'),
        known=session.get('known', False),
        email_status=session.pop('email_status', None),
        editing_id=session.get('editing_id')
    )


# Ativa o modo de edição na própria tabela
@main.route('/users/<int:id>/edit-mode', methods=['POST'])
def edit_mode(id):
    user = db.session.get(User, id)

    if user is None:
        session['email_status'] = 'Usuário não encontrado.'
    else:
        session['editing_id'] = user.id

    return redirect(url_for('.index'))


# Cancela a edição
@main.route('/users/<int:id>/cancel-edit', methods=['POST'])
def cancel_edit(id):
    session.pop('editing_id', None)

    return redirect(url_for('.index'))


# Salva as alterações
@main.route('/users/<int:id>/edit', methods=['POST'])
def edit_user(id):
    user = db.session.get(User, id)

    if user is None:
        session['email_status'] = 'Usuário não encontrado.'
        session.pop('editing_id', None)

        return redirect(url_for('.index'))

    form = EditUserForm()

    roles = Role.query.order_by(Role.name.asc()).all()

    form.role_id.choices = [
        (role.id, role.name)
        for role in roles
    ]

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        # Verifica se outro usuário já utiliza o nome ou e-mail.
        existing_user = User.query.filter(
            User.id != user.id,
            or_(
                User.username == username,
                User.email == email
            )
        ).first()

        if existing_user:
            session['email_status'] = (
                'Já existe outro usuário com esse nome ou e-mail.'
            )

            session['editing_id'] = user.id

            return redirect(url_for('.index'))

        try:
            user.username = username
            user.email = email
            user.role_id = form.role_id.data

            db.session.commit()

            session.pop('editing_id', None)

            session['name'] = username
            session['email_status'] = (
                'Usuário atualizado com sucesso!'
            )

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                'Erro ao atualizar usuário.'
            )

            session['email_status'] = (
                'Não foi possível atualizar o usuário.'
            )

            session['editing_id'] = user.id

    else:
        current_app.logger.warning(
            'Erros de validação ao editar usuário %s: %s',
            id,
            form.errors
        )

        session['email_status'] = (
            'Verifique os dados informados.'
        )

        session['editing_id'] = user.id

    return redirect(url_for('.index'))


# Exclui um usuário
@main.route('/users/<int:id>/delete', methods=['POST'])
def delete_user(id):
    form = DeleteUserForm()

    if not form.validate_on_submit():
        session['email_status'] = (
            'Não foi possível validar a solicitação de exclusão.'
        )

        return redirect(url_for('.index'))

    user = db.session.get(User, id)

    if user is None:
        session['email_status'] = 'Usuário não encontrado.'

        return redirect(url_for('.index'))

    try:
        username = user.username

        db.session.delete(user)
        db.session.commit()

        session.pop('editing_id', None)

        session['email_status'] = (
            f'Usuário "{username}" excluído com sucesso.'
        )

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            'Erro ao excluir usuário.'
        )

        session['email_status'] = (
            'Não foi possível excluir o usuário.'
        )

    return redirect(url_for('.index'))