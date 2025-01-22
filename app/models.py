from . import db
from flask_login import UserMixin
from datetime import datetime
import json

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
    __tablename__ = 'contracts'  # Optional, specifies the table name

    # Attributes matching the keys you provided
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True, nullable=False)  # 'active'
    startDate = db.Column(db.String(10), nullable=False)  # 'startDate' in 'YYYY-MM-DD'
    endDate = db.Column(db.String(10), nullable=False)  # 'endDate' in 'YYYY-MM-DD'
    failedMembers = db.Column(db.Text, default=json.dumps([]), nullable=False)  # 'failedMembers'
    image = db.Column(db.String(255))  # 'image' for the group picture
    lastMessage = db.Column(db.Text, default=json.dumps({}), nullable=False)  # 'lastMessage'
    members = db.Column(db.Text, default=json.dumps([]), nullable=False)  # 'members' JSON-encoded list
    invitedUsers = db.Column(db.Text, default=json.dumps([]), nullable=False)  # 'invitedUsers' JSON-encoded list
    name = db.Column(db.String(100), nullable=False)  # 'name' for contract name
    progressInterval = db.Column(db.String(20), nullable=False)  # 'progressInterval'
    progressIntervalDeadline = db.Column(db.String(10), nullable=False)  # 'progressIntervalDeadline' in 'YYYY-MM-DD'
    progressIntervalsCompleted = db.Column(db.Text, default=json.dumps({}), nullable=False)  # 'progressIntervalsCompleted'

    # Relationships for backreferences
    tasks = db.relationship('Task', backref='contract', lazy=True)  # Link to tasks
    messages = db.relationship('Message', backref='contract', lazy=True)  # Link to messages
    progressUpdates = db.relationship('ProgressUpdate', backref='contract', lazy=True)  # Link to progress updates

    # Optional __repr__ for debugging
    def __repr__(self):
        return f"<Contract {self.name}>"


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)  # Foreign key to Contract
    active = db.Column(db.Boolean, default=True, nullable=False)  # Task is active or not
    interval = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', etc.
    intervalDeadline = db.Column(db.String(10), nullable=False)  # Deadline in 'YYYY-MM-DD'
    intervalsTot = db.Column(db.Integer, nullable=False)  # Total intervals for the task
    intervalsCompleted = db.Column(db.Text, default=json.dumps({}), nullable=False)  # JSON-encoded dict
    repsTot = db.Column(db.Integer, nullable=False)  # Total reps for the task
    repsCompleted = db.Column(db.Text, default=json.dumps({}), nullable=False)  # JSON-encoded dict
    name = db.Column(db.String(100), nullable=False)  # Task name

    def __repr__(self):
        return f"<Task {self.name}>"




class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    sender = db.relationship('User', backref='messages')
    contract = db.relationship('Contract', back_populates='messages')


