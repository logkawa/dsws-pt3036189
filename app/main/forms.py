from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length


class NameForm(FlaskForm):
    name = StringField(
        'Qual é o seu nome?',
        validators=[
            DataRequired(),
            Length(min=1, max=64)
        ]
    )

    email = StringField(
        'Qual é o seu email (Envio de notificação do novo usuário)?',
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    submit = SubmitField('Submit')


class EditUserForm(FlaskForm):
    username = StringField(
        'Nome do usuário',
        validators=[
            DataRequired(message='Informe o nome do usuário.'),
            Length(min=1, max=64)
        ]
    )

    email = StringField(
        'E-mail',
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    role_id = SelectField(
        'Função',
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField('Salvar')


class DeleteUserForm(FlaskForm):
    submit = SubmitField('Excluir')