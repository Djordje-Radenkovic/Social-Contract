from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Contract, Message
from . import db

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def contracts():
    stories = [
        {"title": "Daily TikTok Post", "background_image": "/static/dummy_images/tiktok.jpg"},
        {"title": "Hackathon", "background_image": "/static/dummy_images//hackathon.jpg"},
        {"title": "Breakup Aid", "background_image": "/static/dummy_images//breakup.jpg"},
        {"title": "Running Club", "background_image": "/static/dummy_images//running.jpg"},
        {"title": "Digital Detox", "background_image": "/static/dummy_images//detox.jpg"},
        {"title": "Gym Bros", "background_image": "/static/dummy_images//gym.jpg"},
        {"title": "Meditation", "background_image": "/static/dummy_images//meditation.jpg"},
    ]

    contracts = [
        {
            "name": "Daily 5k run",
            "progressInterval": "Week",
            "progressIntervalsCompleted": 3,
            'image': "static/dummy_images/Masha.jpg",
            'lastMessage': {
                'sender':'Masha',
                'messageReadByMe': False,
                'timeReceived': '13:43',
                'type': 'completion'
            },
            'tasks': [
                {
                    'name': 'Go for a run',
                    'repsTotal': 3,
                    'repsCompleted': 2,
                    'intervalDeadline': 'by Sunday'
                },
                {   
                    'name': 'Eat protein',
                    'repsTotal': 1,
                    'repsCompleted': 0,
                    'intervalDeadline': 'Today'
                },
                {
                    'name': 'Run a 10k',
                    'repsTotal': 1,
                    'repsCompleted': 1,
                    'intervalDeadline': 'by Friday'
                }
            ]
         },
         {
             'name': 'Digital Detox',
             'progressInterval': 'Day',
             'progressIntervalsCompleted': 31,
             'image': 'static/dummy_images/Bogdan.jpg',
             'lastMessage': {
                'sender':'Bogdan',
                'messageReadByMe': True,
                'timeReceived': '12:31',
                'type': 'message'
            },
            'tasks': [
                {
                    'name': 'No Youtube',
                    'repsTotal': 1,
                    'repsCompleted': 0,
                    'intervalDeadline': 'Today'
                },
                {
                    'name': 'No podcasts',
                    'repsTotal': 1,
                    'repsCompleted': 1,
                    'intervalDeadline': 'Today'
                }
            ]
         }
    ]

    return render_template('contracts.html', user=current_user, stories=stories, contracts=contracts)

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))
    return render_template('signup.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.contracts'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.login'))

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@main.route('/profile', methods=['POST'])
@login_required
def update_profile():
    new_username = request.form['username']
    current_user.username = new_username
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('main.profile'))

############# CONTRACTS ##############

@main.route('/create_contract', methods=['POST'])
def create_contract():
    data = request.get_json()
    contract_name = data.get('name')
    member_ids = data.get('members')  # List of user IDs

    if not contract_name or not member_ids:
        return jsonify({"error": "Contract name and members are required"}), 400

    contract = Contract(name=contract_name)
    for user_id in member_ids:
        user = User.query.get(user_id)
        if user:
            contract.members.append(user)

    db.session.add(contract)
    db.session.commit()

    return jsonify({"message": f"Group '{contract_name}' created successfully!"}), 201

# send message
@main.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    contract_id = data.get('contract_id')
    sender_id = data.get('sender_id')
    content = data.get('content')

    if not contract_id or not sender_id or not content:
        return jsonify({"error": "Group ID, sender ID, and content are required"}), 400

    message = Message(content=content, sender_id=sender_id, group_id=contract_id)
    db.session.add(message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully!"}), 201

# get messages from Contract
@main.route('/get_messages/<int:contract_id>', methods=['GET'])
def get_messages(contract_id):
    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    messages = Message.query.filter_by(contract_id=contract_id).order_by(Message.created_at).all()
    return jsonify([
        {
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "sender_name": message.sender.username,
            "created_at": message.created_at.isoformat()
        }
        for message in messages
    ])
