from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Contract, Message, Task
from . import db
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv
import json
import os
from .helpers import get_next_sunday, task_details, contract_details, get_intervalsTot, format_message_date, format_due_date

main = Blueprint('main', __name__)

# load environmental vaiables
load_dotenv()

# get AWS access
aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')

# set up content database endpoint
s3 = boto3.client(
    's3',
    aws_access_key_id = aws_access_key,
    aws_secret_access_key = aws_secret_key
)
bucket = 'socialcontract1'

################ NAVIGATION ###############



@main.route('/')
@login_required
def contracts():

    # Query contracts the user is a member of
    member_contracts = Contract.query.filter(Contract.members.any(id=current_user.id)).all()

    # Query contracts the user is invited to
    invited_contracts = Contract.query.filter(Contract.invited_users.any(id=current_user.id)).all()

    stories = [
        {"title": "Daily TikTok Post", "background_image": "/static/dummy_images/tiktok.jpg"},
        {"title": "Hackathon", "background_image": "/static/dummy_images//hackathon.jpg"},
        {"title": "Breakup Aid", "background_image": "/static/dummy_images//breakup.jpg"},
        {"title": "Running Club", "background_image": "/static/dummy_images//running.jpg"},
        {"title": "Digital Detox", "background_image": "/static/dummy_images//detox.jpg"},
        {"title": "Gym Bros", "background_image": "/static/dummy_images//gym.jpg"},
        {"title": "Meditation", "background_image": "/static/dummy_images//meditation.jpg"},
    ]

    contracts = 2*[
        {
            "id": '12345',
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
             'id': '123456',
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

    interval_map = {
        "daily": 'Day',
        'weekly': 'Week',
        'once': 'Milestone'
    }

    contracts = [
            {
                "id": contract.id,
                "name": contract.name,
                "progressInterval": interval_map[contract.progressInterval],
                "progressIntervalsCompleted": json.loads(contract.progressIntervalsCompleted)[current_user.username],
                "image": contract.image,
                "lastMessage": format_message_date(json.loads(contract.lastMessage)),
                "tasks": [
                    {
                        "name": task.name,
                        "repsTotal": task.repsTot,
                        "repsCompleted": json.loads(task.repsCompleted)[current_user.username],
                        "intervalDeadline": format_due_date(task.intervalDeadline)
                    }
                    for task in contract.tasks 
                ]
            }
            for contract in member_contracts + invited_contracts
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

@main.route('/contract/<int:contract_id>', methods=['GET'])
@login_required
def contract_group_chat(contract_id):
    contract = Contract.query.get(contract_id)
    if not contract:
        flash("Contract not found.", "danger")
        return redirect(url_for('main.contracts'))

    if current_user not in contract.members:
        flash("You are not a member of this contract.", "danger")
        return redirect(url_for('main.contracts'))

    return render_template('group_chat.html', contract=contract, user=current_user)


############# CONTRACTS ##############


@main.route('/create_contract', methods=['POST'])
def create_contract():
    print("Form data:", request.form)
    print("File data:", request.files)

    # Extract data
    background_image = request.files.get('background_image')  # Background image
    contract_name = request.form.get('name')  # Contract name
    expiry = request.form.get('expiry')  # Contract expiry date (string format)
    visibility = request.form.get('visibility')  # Visibility (public/private)
    members = request.form.get('members', '[]')  # List of usernames if private, empty if public
    tasks = request.form.get('tasks')

    # Validate input data
    if not contract_name or not expiry or not tasks:
        return jsonify({'error': 'Contract name, expiry, and tasks are required'}), 400

    tasks = json.loads(tasks)
    if not tasks or any(task.get('name', '').strip() == '' for task in tasks):
        return jsonify({'error': 'At least one valid task is required.'}), 400

    # Process members
    members = json.loads(members)
    if visibility == 'private' and not members:
        return jsonify({'error': 'Private contracts must have at least one member.'}), 400

    # Query the current user
    current_user_obj = User.query.filter_by(username=current_user.username).first()
    if not current_user_obj:
        return jsonify({'error': 'Current user not found.'}), 400

    # Upload background image to AWS and retrieve URL
    if background_image:
        filename = secure_filename(background_image.filename)
        address = f'groupPictures/{filename}'
        s3.upload_fileobj(background_image, bucket, address)
        groupPicture = f"https://{bucket}.s3.amazonaws.com/{address}"
    else:
        groupPicture = None

    # Compute contract details
    contract_dets = contract_details(tasks)

    progressIntervalsCompleted = {str(name): 0 for name in members + [current_user.username]}

    lastMessage = {
                    'sender': current_user.username,
                    'messageReadBy': [current_user.username],
                    'timeReceived': datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                    'type': 'initiation'
                }

    # Create the contract instance
    new_contract = Contract(
        active=True,
        startDate=datetime.utcnow().strftime('%Y-%m-%d'),
        endDate=expiry,
        failedMembers=json.dumps([]),
        image=groupPicture,
        lastMessage=json.dumps(lastMessage),
        name=contract_name,
        progressInterval=contract_dets['progressInterval'],
        progressIntervalDeadline=contract_dets['progressIntervalDeadline'],
        progressIntervalsCompleted=json.dumps(progressIntervalsCompleted)
    )

    # Add the current user as a member
    new_contract.members.append(current_user_obj)

     # Add other users as invited
    for username in members:
        user = User.query.filter_by(username=username).first()
        if user:
            new_contract.invited_users.append(user)

    # Add the contract to the database
    db.session.add(new_contract)
    db.session.commit()

    # Retrieve the contract ID
    contract_id = new_contract.id

    # Add tasks to the database
    for task in tasks:
        task_dets = task_details(task)
        new_task = Task(
            contract_id=contract_id,
            active=True,
            interval=task_dets['interval'],
            intervalDeadline=task_dets['intervalDeadline'],
            intervalsTot=get_intervalsTot(contract_dets['progressInterval'], task_dets['interval']),
            intervalsCompleted=json.dumps(progressIntervalsCompleted),
            repsTot=task_dets['repsTot'],
            repsCompleted=json.dumps(progressIntervalsCompleted),
            name=task['name']
        )
        db.session.add(new_task)

    db.session.commit()

    # Return success response with contract ID
    return jsonify({
        'message': 'Contract created successfully!',
        'contract_id': contract_id,
        'image_path': new_contract.image
    }), 200


@main.route('/get_users', methods=['GET'])
@login_required
def get_users():
    # Query all users except the current user
    users = User.query.filter(User.id != current_user.id).all()

    # Format the users into a list of dictionaries
    user_data = [
        {
            "id": user.id,  # User ID
            "username": user.username,  # Username
            "picture": user.picture_url if hasattr(user, 'picture_url') else None  # Picture URL or None
        }
        for user in users
    ]

    return jsonify(user_data)  # Return the list as a JSON response


############# MESASGING ##############

# send message
@main.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    contract_id = data.get('contract_id')
    sender_id = data.get('sender_id')
    content = data.get('content')

    if not contract_id or not sender_id or not content:
        return jsonify({"error": "Contract ID, sender ID, and content are required"}), 400

    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    sender = User.query.get(sender_id)
    if sender not in contract.members:
        return jsonify({"error": "Sender is not a member of this contract"}), 403

    message = Message(content=content, sender_id=sender_id, contract_id=contract_id)
    db.session.add(message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully!"}), 201

# read messages
@main.route('/get_messages/<int:contract_id>', methods=['GET'])
def get_messages(contract_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    messages = Message.query.filter_by(contract_id=contract_id).order_by(Message.created_at).paginate(page=page, per_page=per_page)
    return jsonify([
        {
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "sender_name": message.sender.username,
            "created_at": message.created_at.isoformat()
        }
        for message in messages.items
    ])

