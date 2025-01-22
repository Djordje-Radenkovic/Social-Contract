from datetime import datetime, timedelta

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