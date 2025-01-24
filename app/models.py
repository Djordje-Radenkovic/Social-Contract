from . import db
from flask_login import UserMixin
from datetime import datetime
import json

# Many-to-Many association table for GroupChat members
contract_members = db.Table('contract_members',
    db.Column('contract_id', db.Integer, db.ForeignKey('contracts.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

invited_users = db.Table(
    'invited_users',
    db.Column('contract_id', db.Integer, db.ForeignKey('contracts.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(201), nullable=False)
    # relationships
    contracts = db.relationship('Contract', secondary=contract_members, back_populates='members')
    invited_to = db.relationship('Contract', secondary=invited_users, back_populates='invited_users')

class Contract(db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    startDate = db.Column(db.String(10), nullable=False)
    endDate = db.Column(db.String(10), nullable=False)
    failedMembers = db.Column(db.Text, default=json.dumps([]), nullable=False)
    image = db.Column(db.String(255))
    lastMessage = db.Column(db.Text, default=json.dumps({}), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    progressInterval = db.Column(db.String(20), nullable=False)
    progressIntervalDeadline = db.Column(db.String(10), nullable=False)
    progressIntervalsCompleted = db.Column(db.Text, default=json.dumps({}), nullable=False)

    # Relationships
    members = db.relationship('User', secondary=contract_members, back_populates='contracts')
    tasks = db.relationship('Task', backref='contract', lazy=True)
    messages = db.relationship('Message', backref='contract', lazy=True)
    invited_users = db.relationship('User', secondary=invited_users, back_populates='invited_to')


    def __repr__(self):
        return f"<Contract {self.name}>"

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    interval = db.Column(db.String(20), nullable=False)
    intervalDeadline = db.Column(db.String(10), nullable=False)
    intervalsTot = db.Column(db.Integer, nullable=False)
    intervalsCompleted = db.Column(db.Text, default=json.dumps({}), nullable=False)
    repsTot = db.Column(db.Integer, nullable=False)
    repsCompleted = db.Column(db.Text, default=json.dumps({}), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Task {self.name}>"

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    sender = db.relationship('User', backref='messages')
