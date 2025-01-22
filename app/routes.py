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
from helpers import get_next_sunday, task_details, contract_details, get_intervalsTot

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

# @main.route('/create_contract', methods=['POST'])
# @login_required
# def create_contract():
#     data = request.json  # Expecting JSON from the frontend
#     contract_name = data.get('name')
#     expiry = data.get('expiry')
#     tasks = data.get('tasks')  # List of tasks with intervals, deadlines, etc.
#     member_ids = data.get('members')
#     visibility = data.get('visibility')

#     if not contract_name or not member_ids or not tasks:
#         return jsonify({'error': 'Contract name, members, and tasks are required.'}), 400

#     # Calculate progress interval from tasks
#     progress_interval = max(task['interval'] for task in tasks)  # Custom logic as needed
#     progress_interval_deadline = calculate_deadline(progress_interval, tasks)  # Implement this function

#     contract = Contract(
#         name=contract_name,
#         end_date=expiry,
#         progress_interval=progress_interval,
#         progress_interval_deadline=progress_interval_deadline,
#         members=[User.query.get(user_id) for user_id in member_ids],
#     )

#     # Add tasks to contract
#     for task_data in tasks:
#         task = Task(
#             title=task_data['title'],
#             interval=task_data['interval'],
#             interval_deadline=task_data['interval_deadline'],
#             intervals_total=task_data['intervals_total'],
#             reps_total=task_data['reps_total'],
#             order=task_data.get('order', '')
#         )
#         contract.tasks.append(task)

#     db.session.add(contract)
#     db.session.commit()

#     return jsonify({'message': 'Contract created successfully!'}), 201


@main.route('/create_contract', methods=['POST'])
def create_contract():
    print("Form data:", request.form)
    print("File data:", request.files)

    # Extract data
    background_image = request.files.get('background_image')  # background image
    contract_name = request.form.get('name') # contract name
    expiry = request.form.get('expiry') # contract expiry date - string form
    visibility = request.form.get('visibility') # visibility - public or private
    members = request.form.get('members', '[]') # list of usernames if private, empty if public
    tasks = request.form.get('tasks')

    # check if input data all good
    if not contract_name or not expiry or not tasks:
        return jsonify({'error': 'Contract name5 is required'}), 400

    tasks = json.loads(tasks)
    if not tasks or any(task.get('name', '').strip() == '' for task in tasks):
        return jsonify({'error': 'At least one valid task is required.'}), 400

    # Process members
    members = json.loads(members)
    if visibility == 'private' and not members:
        return jsonify({'error': 'Private contracts must have at least one member.'}), 400

    # Upload background image to AWS and retreive URl
    if background_image:
        filename = secure_filename(background_image.filename)
        address = f'groupPictures/{filename}'
        s3.upload_fileobj(background_image, bucket, address )
        # Generate S3 URL
        groupPicture= f"https://{bucket}.s3.amazonaws.com/{address}"
    else:
        groupPicture = None
    
    # compute some contract details
    contract_details = contract_details(tasks)
    progressIntervalsCompleted = {name: 0 for name in members + current_user.username}

    # Create a Contract instance
    new_contract = Contract(
        active=True,
        startDate=datetime.utcnow().strftime('%Y-%m-%d'),
        endDate=expiry,
        failedMembers=json.dumps([]),
        image=groupPicture,
        lastMessage=json.dumps({}),
        members=json.dumps([current_user.username]),
        invitedUsers=json.dumps(members),
        name=contract_name,
        progressInterval=contract_details['progressInterval'],
        progressIntervalDeadline=contract_details['progressIntervalDeadline'],
        progressIntervalsCompleted=json.dumps(progressIntervalsCompleted)
    )

    # Add and commit the contract to the database
    db.session.add(new_contract)
    db.session.commit()

    # Retrieve the contract ID
    contract_id = new_contract.id

    for task in tasks:
        task_details = task_details(task)
        # Tasks
        new_task = Task(
            contract_id=contract_id,
            active=True,
            interval=task_details['interval'],
            intervalDeadline=task_details['intervalDeadline'],
            intervalsTot=get_intervalsTot(contract_details['progressInterval'], task_details['interval']),
            intervalsCompleted=json.dumps(progressIntervalsCompleted),
            repsTot=task_details['repsTot'],
            repsCompleted=json.dumps(progressIntervalsCompleted),
            name=task_details['name']
        )
        db.session.add(new_task)
    db.session.commit() 

    # Return success response with contract ID
    return jsonify({
        'message': 'Contract and tasks created successfully!',
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

