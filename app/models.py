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

# class Contract(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     active = db.Column(db.Boolean, default=True)
#     start_date = db.Column(db.DateTime, default=datetime.utcnow)
#     end_date = db.Column(db.DateTime)
#     group_picture = db.Column(db.String, nullable=True)
#     progress_interval = db.Column(db.String, nullable=False)  # daily/weekly/once
#     progress_interval_deadline = db.Column(db.String, nullable=True)
#     progress_intervals_completed = db.Column(db.JSON, default={})
#     members = db.relationship('User', secondary=contract_members, back_populates='contracts')
#     tasks = db.relationship('Task', backref='contract', cascade="all, delete-orphan")
#     last_message = db.Column(db.JSON, default={})
#     failed_members = db.Column(db.JSON, default=[])
#     invited_users = db.Column(db.JSON, default=[])  # List of emails
#     member_details = db.Column(db.JSON, default={})


# class Task(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String, nullable=False)
#     interval = db.Column(db.String, nullable=False)  # daily/weekly/once
#     interval_deadline = db.Column(db.String, nullable=True)
#     intervals_total = db.Column(db.Integer, nullable=False, default=1)
#     intervals_completed = db.Column(db.JSON, default={})  # {user_id: completed_intervals}
#     reps_total = db.Column(db.Integer, nullable=False, default=1)
#     reps_completed = db.Column(db.JSON, default={})  # {user_id: reps_completed}
#     order = db.Column(db.String, nullable=True)
#     contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    sender = db.relationship('User', backref='messages')
    contract = db.relationship('Contract', back_populates='messages')


