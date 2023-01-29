from datetime import date, timedelta

def current_week():
    today = date.today()
    weekday = today.weekday()
    start_delta = timedelta(days=weekday)
    start_of_week = today - start_delta

    week = []

    for i in range(7):
        days = start_of_week + timedelta(days=i)
        week.append(days.strftime('%m/%d/%Y').lstrip('0'))

    return week