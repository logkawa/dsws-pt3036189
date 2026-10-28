from . import db


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    users = db.relationship('User', back_populates='role')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(64),
        unique=True,
        index=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        index=True,
        nullable=False
    )

    role_id = db.Column(
        db.Integer,
        db.ForeignKey('roles.id'),
        nullable=False
    )

    role = db.relationship('Role', back_populates='users')

    def __repr__(self):
        return f'<User {self.username}>'