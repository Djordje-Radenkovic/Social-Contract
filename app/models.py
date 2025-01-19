from . import db
from flask_login import UserMixin
from datetime import datetime

# Many-to-Many association table for GroupChat members
contract_members= db.Table('contract_members',
    db.Column('contract_id', db.Integer, db.ForeignKey('contract.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(201), nullable=False)
    contracts = db.relationship('Contract', secondary=contract_members, back_populates='members')


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    members = db.relationship('User', secondary=contract_members, back_populates='contracts')
    messages = db.relationship('Message', back_populates='contract', cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    sender = db.relationship('User', backref='messages')
    contract = db.relationship('Contract', back_populates='messages')


