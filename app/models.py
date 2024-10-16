from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy import inspect, Table, UniqueConstraint, Boolean
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import datetime

# Add this at the top of the file
user_transaction_models = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.id, salt=current_app.config['SECURITY_PASSWORD_SALT'])

    @staticmethod
    def verify_confirmation_token(token, expiration=3600):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = serializer.loads(
                token,
                salt=current_app.config['SECURITY_PASSWORD_SALT'],
                max_age=expiration
            )
        except:
            return None
        return User.query.get(user_id)

    def confirm_email(self):
        self.confirmed = True
        self.confirmed_on = datetime.datetime.now()
        db.session.add(self)
        db.session.commit()

class UserTransaction(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    transaction_description = db.Column(db.String(255), nullable=False)
    paid_in = db.Column(db.Float)
    paid_out = db.Column(db.Float)
    comment = db.Column(db.Text)
    invoice = db.Column(db.String(255))
    vat = db.Column(db.Float)
    highlight = db.Column(db.Boolean, default=False)  # New column

    @classmethod
    def create_table(cls, user_id):
        table_name = f"user_transactions_{user_id}"
        
        if table_name in user_transaction_models:
            return user_transaction_models[table_name]
        
        if inspect(db.engine).has_table(table_name):
            # If the table exists, return the existing model
            metadata = db.Model.metadata
            table = Table(table_name, metadata, autoload_with=db.engine)
            model = type(table_name, (cls,), {'__table__': table})
        else:
            # If the table doesn't exist, create a new model
            model = type(table_name, (cls,), {
                '__tablename__': table_name,
                'user_id': db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False),
                'highlight': db.Column(db.Boolean, default=False),  # Add the new column here as well
                '__table_args__': (
                    UniqueConstraint('user_id', 'date', 'transaction_description', 'paid_in', 'paid_out', name=f'uix_{table_name}'),
                )
            })
            # Create the table
            model.__table__.create(db.engine, checkfirst=True)
        
        user_transaction_models[table_name] = model
        return model

    @classmethod
    def get_user_model(cls, user_id):
        table_name = f"user_transactions_{user_id}"
        if table_name not in user_transaction_models:
            cls.create_table(user_id)
        return user_transaction_models.get(table_name)
