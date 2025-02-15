from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Contract, Message, Task
from . import db
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv
from app import socketio
import json
import pytz
from flask_socketio import emit, join_room
import os
from .helpers import get_next_sunday, task_details, contract_details, get_intervalsTot, format_message_date, format_due_date
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import base64
import time
from solana.rpc.api import Client
from openai import OpenAI
import uuid


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

# set up solana client
solana_client = Client("https://api.devnet.rpcpool.com")


# initialise the client
client = OpenAI()


################ NAVIGATION ###############

import hashlib

def get_contract_gradient(contract_name):
    # Generate a hash from the contract name
    hash_value = int(hashlib.md5(contract_name.encode()).hexdigest(), 16)  

    # Use hash to pick a highly varied hue (0-360°) for strong differences
    hue = hash_value % 360  
    
    # Set saturation and lightness values
    saturation = 70  # 70% for vibrant color
    lightness1 = 65  # Lighter shade
    lightness2 = 45  # Darker shade for gradient

    # Convert to HSL format for CSS
    color1 = f"hsl({hue}, {saturation}%, {lightness1}%)"
    color2 = f"hsl({hue}, {saturation}%, {lightness2}%)"

    return f'linear-gradient(135deg, {color1}, {color2})'



@main.route('/')
@login_required
def contracts():

    # Query contracts the user is a member of
    member_contracts = Contract.query.filter(Contract.members.any(id=current_user.id)).all()

    # Query contracts the user is invited to
    invited_contracts = Contract.query.filter(Contract.invited_users.any(id=current_user.id)).all()

    public_stories_contracts = (
        db.session.query(Contract)
        .join(Message)
        .filter(Contract.visibility == 'public')
        .filter(Message.contract_id == Contract.id, Message.media_url.isnot(None))
        .distinct()
        .all()
    )
    
    

    # Map public stories data
    stories = [
        {
            "id": contract.id,
            "gradient": get_contract_gradient(contract.name),
            "name": contract.name,
            "image": Message.query.filter_by(contract_id=contract.id).filter(Message.media_url.isnot(None)).all()[-1].media_url, #contract.image,
        }
        for contract in public_stories_contracts
    ]
   

    interval_map = {
        "daily": 'Day',
        'weekly': 'Week',
        'once': 'Milestone'
    }


    contracts = [
            {
                "id": contract.id,
                "gradient": get_contract_gradient(contract.name),
                "active": contract.active,
                "name": contract.name,
                "progressInterval": interval_map[contract.progressInterval],
                "progressIntervalsCompleted": json.loads(contract.progressIntervalsCompleted)[current_user.username],
                "image": contract.image,
                "lastMessage": format_message_date(json.loads(contract.lastMessage), current_user.timezone),
                "tasks": [
                    {   
                        "id": task.id,
                        "name": task.name,
                        "repsTotal": task.repsTot,
                        "repsCompleted": json.loads(task.repsCompleted)[current_user.username],
                        "intervalDeadline": format_due_date(task.intervalDeadline)
                    }
                    for task in contract.tasks 
                ],
                "has_stories": len(
                    Message.query.filter_by(contract_id=contract.id)
                    .filter(Message.media_url.isnot(None))
                    .all()
                ) > 0
            }
            for contract in member_contracts + invited_contracts
    ]

    user_agent = request.user_agent.string.lower()
    print(user_agent)
    
    if "mobile" in user_agent:
        return render_template('contracts.html', user=current_user, stories=stories, contracts=contracts)
    else:
        return render_template('desktop.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # generate new Solana wallet
        keypair = Keypair()
        public_key = str(keypair.pubkey())
        private_key = base64.b64encode(bytes(keypair)).decode('utf-8')

        new_user = User(username=username, 
                        password=hashed_password, 
                        solana_public_key=public_key, 
                        solana_private_key=private_key)
        
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
    user_agent = request.user_agent.string.lower()
    print(user_agent)
    
    if "mobile" in user_agent:
        return render_template('login.html')
    else:
        return render_template('desktop.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.login'))

@main.route('/profile')
@login_required
def profile():
    cur_user = User.query.filter_by(username=current_user.username).first()
    balance = cur_user.balance
    address = cur_user.solana_public_key
    return render_template('profile.html', user=current_user, balance = balance, sol_address=address)

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
    
    tasks = contract.tasks
    if not tasks:
        flash('Tasks not found')

    if current_user not in contract.members and current_user not in contract.invited_users:
        flash("You are not a member of this contract.", "danger")
        return redirect(url_for('main.contracts'))

    return render_template('group_chat.html', contract=contract, user=current_user, tasks=tasks)

@main.route('/contract/<int:contract_id>/accept', methods=['POST'])
@login_required
def accept_invitation(contract_id):
    contract = Contract.query.get(contract_id)
    if not contract or current_user not in contract.invited_users:
        return jsonify({"error": "Invalid or unauthorized action"}), 403

    # Remove from invited_users and add to members
    contract.invited_users.remove(current_user)
    contract.members.append(current_user)
    db.session.commit()

    return jsonify({"message": "Invitation accepted"})

@main.route('/contract/<int:contract_id>/decline', methods=['POST'])
@login_required
def decline_invitation(contract_id):
    contract = Contract.query.get(contract_id)
    if not contract or current_user not in contract.invited_users:
        return jsonify({"error": "Invalid or unauthorized action"}), 403

    # Remove from invited_users
    contract.invited_users.remove(current_user)
    db.session.commit()

    return jsonify({"message": "Invitation declined"})


@main.route('/set_timezone', methods=['POST'])
@login_required
def set_timezone():
    data = request.get_json()
    timezone = data.get('timezone')

    # Validate the timezone
    if timezone not in pytz.all_timezones:
        return jsonify({"error": "Invalid timezone"}), 400

    # Update the user's timezone in the database
    user = current_user  # Assuming Flask-Login is being used
    user.timezone = timezone
    db.session.commit()

    return jsonify({"message": "Timezone updated successfully"}), 200



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
        progressIntervalsCompleted=json.dumps(progressIntervalsCompleted),
        visibility= visibility
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
    content = data.get('content', "").strip()  # Optional text content
    media_url = data.get('media_url', None) 

    # Validate inputs
    if not contract_id or not sender_id or (not content and not media_url):
        return jsonify({"error": "Contract ID, sender ID, and either content or media_url are required"}), 400

    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404
    
    # Save the message
    message = Message(
        content=content if content else None,
        media_url=media_url if media_url else None,
        sender_id=sender_id,
        contract_id=contract_id,
    )
    db.session.add(message)

    # Update lastMessage in the contract
    contract.lastMessage = json.dumps({
        'sender': sender.username,
        'messageReadBy': [sender.username],
        'timeReceived': datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        'type': 'message'
    })

    db.session.commit()

    return jsonify({"message": "Message sent successfully!", "message_id": message.id}), 201


# read messages
@main.route('/get_messages/<int:contract_id>', methods=['GET'])
def get_messages(contract_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)

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
            "created_at": message.created_at.isoformat(),
            "media_url": message.media_url,
            "ai_verified": message.ai_verified,
            "task_name": Task.query.get(message.task_id).name if Task.query.get(message.task_id) else None
        }
        for message in messages.items
    ])

# Socketio messaging

@socketio.on('send_message')
def handle_send_message(data):
    contract_id = data.get('contract_id')
    sender_id = data.get('sender_id')
    content = data.get('content')
    media_url = data.get('media_url')

    # Validate inputs
    if not contract_id or not sender_id or (not content and not media_url):
        emit('error', {"message": "Contract ID, sender ID, and either content or media_url are required"}, broadcast=False)
        return

    # Fetch sender and contract
    sender = User.query.get(sender_id)
    if not sender:
        emit('error', {"message": "Invalid sender ID"}, broadcast=False)
        return

    contract = Contract.query.get(contract_id)
    if not contract:
        emit('error', {"message": "Invalid contract ID"}, broadcast=False)
        return

    # Check if sender is a member of the contract
    if sender not in contract.members:
        emit('error', {"message": "Sender is not a member of the contract"}, broadcast=False)
        return

    # Save the message
    message = Message(
        content=content if content else None,
        media_url=media_url if media_url else None,
        sender_id=sender_id,
        contract_id=contract_id,
    )

    db.session.add(message)

    # Update lastMessage in the contract
    contract.lastMessage = json.dumps({
        'sender': sender.username,
        'messageReadBy': [sender.username],
        'timeReceived': datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        'type': 'message'
    })

    db.session.commit()

    # Emit the message to the room
    emit('new_message', {
        "id": message.id,
        "content": message.content,
        "sender_id": message.sender_id,
        "sender_name": sender.username,  # Use sender directly
        "created_at": message.created_at.isoformat(),
        "media_url": message.media_url
    }, room=f"contract_{contract_id}")


@socketio.on('join')
def handle_join(data):
    contract_id = data.get('contract_id')
    join_room(f"contract_{contract_id}")

@main.route('/mark_message_seen/<int:contract_id>', methods=['POST'])
@login_required
def mark_message_seen(contract_id):
    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    # Load the current lastMessage
    last_message = json.loads(contract.lastMessage)
    if current_user.username not in last_message['messageReadBy']:
        last_message['messageReadBy'].append(current_user.username)

        # Update the contract's lastMessage
        contract.lastMessage = json.dumps(last_message)
        db.session.commit()

    return jsonify({"message": "Message marked as seen"})

@main.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    image = request.files.get('image')
    if not image:
        return jsonify({"error": "No image provided"}), 400

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")  # Example: 2025-02-12_23-59-59
    unique_id = uuid.uuid4().hex[:8]  # Short unique identifier
    file_extension = image.filename.rsplit('.', 1)[-1].lower()  # Extract file extension

    ###########################
    contract_id = request.form.get('contract_id')  # Pass contract_id from frontend
    sender_id = request.form.get('sender_id')  # Pass sender_id from frontend
    task_id = request.form.get('task_id')

    #filename = secure_filename(image.filename)
    filename = f"{current_user.username}_{contract_id}_{timestamp}_{unique_id}.{file_extension}"
    address = f'message_images/{filename}'
    s3.upload_fileobj(image, bucket, address)
    media_url = f"https://{bucket}.s3.amazonaws.com/{address}"




    # Save the message with the media URL in the database
    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    sender = User.query.get(sender_id)
    if sender not in contract.members:
        return jsonify({"error": "Sender is not a member of this contract"}), 403
    
    ai_verified = True
    if int(contract_id) == 1 and int(task_id) == 1:
        print('CIAO')
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Does this image show total daily use time below 2h? Only answer Yes or No."},
                        {"type": "image_url", "image_url": {"url": media_url}},
                    ],
                }
            ],
            max_tokens=10,
        )

        gpt_answer = response.choices[0].message.content.strip().lower()
        print(gpt_answer)

        if "no" in gpt_answer:
            ai_verified = False
            # return jsonify({"error": "Usage time is above 2h. Try again."}), 400

    # send the user a reward
    # sender.solana_p
    # sender.solana_public_key
    # receiver_pubkey = Pubkey.from_string(sender.solana_public_key)
    # airdrop_amount = 10_000_000 
    # response = solana_client.request_airdrop(receiver_pubkey, airdrop_amount)
    sender.balance += 1

    # Validate task_id if provided
    task = None
    if task_id:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        if ai_verified:
            # Update repsCompleted dictionary
            reps_completed = json.loads(task.repsCompleted)
            reps_completed[current_user.username] += 1
            task.repsCompleted = json.dumps(reps_completed)
    
     # Update lastMessage in the contract
    contract.lastMessage = json.dumps({
        'sender': sender.username,
        'messageReadBy': [sender.username],
        'timeReceived': datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        'type': 'completion'
    })

    # Create the message object
    message = Message(content=None,  # No text
                      media_url=media_url,
                      sender_id=sender_id,
                      contract_id=contract_id,
                      task_id=task_id,
                      ai_verified = ai_verified)
    db.session.add(message)
    db.session.commit()

    print('AI verified:', ai_verified)
    # Emit the message via WebSocket
    socketio.emit('new_message', {
        "id": message.id,
        "content": message.content,
        "sender_id": message.sender_id,
        "sender_name": sender.username,
        "created_at": message.created_at.isoformat(),
        "media_url": message.media_url,
        "task_id": task_id,
        "task_name": task.name if task else None,
        "ai_verified": ai_verified
    }, room=f"contract_{contract_id}")


    ################################

    return jsonify({"media_url": media_url}), 201



############## CONTRACT STORIES ################

@main.route('/contract/<int:contract_id>/stories')
def contract_stories(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    messages = Message.query.filter_by(contract_id=contract_id).filter(Message.media_url.isnot(None)).all()
    user_is_member = current_user.username in [user.username for user in contract.members]
    print('user is mamber', user_is_member)
    stories = [
        {
            "media_url": message.media_url,
            "username": message.sender.username,
            "timestamp": message.created_at,
            "task_name": Task.query.get(message.task_id).name if message.task_id else None
        }
        for message in messages
    ]
    return render_template('contract_stories.html', contract=contract, stories=stories, user_is_member=user_is_member)

@main.route('/join_contract/<int:contract_id>', methods=['POST'])
@login_required
def join_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    if contract.visibility != 'public':
        return jsonify({"success": False, "error": "Contract is private"}), 403

    if current_user in contract.members:
        return jsonify({"success": False, "error": "You are already a member"}), 400

    # Add the user to the contract
    contract.members.append(current_user)

     # Update progressIntervalsCompleted
    progress_intervals = json.loads(contract.progressIntervalsCompleted)
    if current_user.username not in progress_intervals:
        progress_intervals[current_user.username] = 0  # Initialize progress for the user
        contract.progressIntervalsCompleted = json.dumps(progress_intervals)

    for task in contract.tasks:
        reps_completed = json.loads(task.repsCompleted)

        if current_user.username not in reps_completed:
            reps_completed[current_user.username] = 0  # Initialize progress for the user

        task.repsCompleted = json.dumps(reps_completed)

    db.session.commit()

    return jsonify({"success": True})
