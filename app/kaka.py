
from .models import User, Contract, Message, Task
from . import db, create_app
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # Perform your database query
    users = User.query.all()
    if users:
        print(f"Last user: {users[-1].username}")
    else:
        print("No users found.")


def get_users_in_first_hour_after_midnight():
    # Fetch all users from the database
    users = User.query.all()  # Adjust this to match your ORM or query method
    users_in_first_hour = []

    for user in users:
        if not user.timezone:
            continue  # Skip users without a timezone

        try:
            # Get the current time in the user's timezone
            user_timezone = pytz.timezone(user.timezone)
            user_time = datetime.now(user_timezone)

            # Check if the user's current time is between midnight and 1:00 AM
            if user_time.hour == 0:
                users_in_first_hour.append(user)

        except pytz.UnknownTimeZoneError:
            print(f"Unknown timezone for user {user.id}: {user.timezone}")
            continue  # Skip users with invalid timezones

    return users_in_first_hour
