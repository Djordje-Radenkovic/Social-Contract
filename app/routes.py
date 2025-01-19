from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Contract, Message
from . import db

main = Blueprint('main', __name__)


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

@main.route('/create_contract', methods=['GET', 'POST'])
@login_required
def create_contract():
    if request.method == 'POST':
        # Get form data
        contract_name = request.form.get('contract_name')
        member_ids = request.form.getlist('members')  # List of user IDs selected

        # Validate input
        if not contract_name or not member_ids:
            flash("Contract name and members are required.", "danger")
            return redirect(url_for('main.create_contract'))

        # Create the contract
        contract = Contract(name=contract_name)
        for user_id in member_ids:
            user = User.query.get(user_id)
            if user:
                contract.members.append(user)

        # Save to database
        db.session.add(contract)
        db.session.commit()

        flash(f"Contract '{contract_name}' created successfully!", "success")
        return redirect(url_for('main.contracts'))  # Redirect to the contracts page

    # Fetch all users to select members
    all_users = User.query.all()
    return render_template('create_contract.html', all_users=all_users)


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

