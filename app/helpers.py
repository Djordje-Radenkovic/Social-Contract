from datetime import datetime, timedelta
import pytz

def format_due_date(date_str):
    # Convert the input string to a date object
    due_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.utcnow().date()
    delta = (due_date - today).days

    if delta == 0:
        return "Today"
    elif 0 < delta <= 6:
        return f"By {due_date.strftime('%A')}"  # Full weekday name (e.g., "By Friday")
    else:
        # Format as "By day Month" (e.g., "By 6 Jan")
        day = due_date.day
        month = due_date.strftime("%b")  # Abbreviated month
        return f"By {day} {month}"  # Outputs e.g., "By 6 Jan"

def format_message_date(lastMessage, user_timezone):
    
    message_date_str = lastMessage["timeReceived"]
    
    # Convert the date string to a datetime object
    message_date = datetime.strptime(message_date_str, "%Y-%m-%d %H:%M")

    # If the user's timezone exists, convert to that timezone
    if user_timezone:
        try:
            user_tz = pytz.timezone(user_timezone)  # Get the user's timezone
            utc = pytz.utc  # UTC timezone
            message_date = utc.localize(message_date)  # Localize the message date to UTC
            message_date = message_date.astimezone(user_tz)  # Convert to user's timezone
        except pytz.UnknownTimeZoneError:
            print(f"Unknown timezone: {user_timezone}. Falling back to UTC.")
            pass  # Leave the message_date in UTC if the timezone is invalid
    

    today = datetime.utcnow()

    # Check if the message date is today
    if message_date.date() == today.date():
        new_time = message_date.strftime("%H:%M")

    # Check if the message date is within the last 6 days
    elif (today - timedelta(days=6)).date() <= message_date.date() < today.date():
        new_time = message_date.strftime("%a")  # Abbreviation for weekday (e.g., 'Mon')

    else:
        # Otherwise, remove leading zeros from the day manually and return 'D Mon' format
        day = int(message_date.strftime("%d"))  # Convert day to integer to remove leading zero
        month = message_date.strftime("%b")  # Get month abbreviation
        new_time = f"{day} {month}"  # Outputs e.g., '8 Jan'
        
    lastMessage["timeReceived"] = new_time
    return lastMessage

def get_next_sunday():
    today = datetime.utcnow()
    days_until_next_sunday = 7 - today.weekday() if today.weekday() == 6 else (6 - today.weekday())
    next_sunday = today + timedelta(days=days_until_next_sunday)
    return next_sunday.strftime('%Y-%m-%d')

def task_details(task):
    frequency = task['frequency']
    if 'Daily' in frequency:
        interval = 'daily'
        repsTot = 1
        intervalDeadline = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d') 
    elif 'week' in frequency:
        interval = 'weekly'
        repsTot = int(frequency.split(' ')[0])
        intervalDeadline = get_next_sunday()
    elif 'By' in frequency:
        interval = 'once'
        repsTot = 1
        intervalDeadline = frequency.split(' ')[-1]

    return {
        'interval': interval,
        'repsTot': repsTot,
        'intervalDeadline': intervalDeadline
        }


def contract_details(tasks): # requires a list of dictionaries (tasks)
    intervals = [task_details(task)['interval'] for task in tasks]    
    
    interval_priority = {
        "once": 0,
        "daily": 1,
        "weekly": 2
    }
    
    progressInterval = max(intervals, key=lambda interval: interval_priority[interval])
    
    if progressInterval == 'daily':
        progressIntervalDeadline = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d') 
    elif progressInterval == 'weekly':
        progressIntervalDeadline = get_next_sunday()
    elif progressInterval =='once':
        soonest = datetime.max
        for t in tasks:
            if 'By' in t['frequency']:
                dat = datetime.strptime(t['frequency'].split(' ')[-1],"%Y-%m-%d") 
                if dat < soonest:
                    soonest = dat
        progressIntervalDeadline = soonest.strftime("%Y-%m-%d")
    
    return {
        'progressInterval': progressInterval,
        'progressIntervalDeadline': progressIntervalDeadline
        }

def get_intervalsTot(progressInterval, interval):
    if progressInterval =='weekly' and interval == 'daily':
        return 7
    else:
        return 1