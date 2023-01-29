import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import gspread as gs
import json
from datetime import timedelta, date, datetime as dt

def get_gsheets(url, sheet_name, json_sa, t_stamp):
    print("[Data] <{0}>: Getting data from google sheets, {1}".format(t_stamp, sheet_name))
    gc = gs.service_account(filename=json_sa)
    sh = gc.open_by_url(url)
    return sh.worksheet(sheet_name)

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

def create_budget_body(df_budget_html, df_essentials_html, weekly_summary_html, cc_dues_html, t_stamp, content):
    print(f'[E-mail] <{t_stamp}>: Creating email body from dataframe')
    pd.set_option('display.max_colwidth', 40)

    print(f'[E-mail] <{t_stamp}>: Creating email content')
    styles = """body{background-color: lightsteelblue}
          h4 {padding-bottom: 4px; margin: 8px; margin-top: 12px;}
          th, td {padding-left: 6px; padding-right: 6px; padding-top: 2px; padding-bottom: 2px; border-style: solid ; border-width: 1px;}
          """

    email_body = f"""
    <!DOCTYPE html>
    <html>
        <head>
        <style>
        {styles}
        </style>
        </head>
        <body>
        <p><b>Good Morning Ilagan Family,</b> 
            <br>
            <br>
            Here's the summary of our budget and expenses. </p>
        <h4>I - Remaining Budget for Personal funds </h4>
        {df_budget_html}
        <h4>II - Remaining Budget for Groceries and Eat Outs.</h4>
        {df_essentials_html}
        <h4>III - Credit Card Balance.</h4>
        {cc_dues_html}
        <h4>IV - Weekly Expenses Summary.</h4>
        {weekly_summary_html}
        <br>
        <i>"Remember to payoff your credit cards before month-end."</i>
        <i>"I wanna be the very best, like no one ever was."</i>
        </body>
    </html>

    """
    print(f'[E-mail] <{t_stamp}>: Saving email into {content}')
    with open(content, 'w') as f:
        f.write(email_body)


# Send email function
def send_mail(params, today, t_stamp):
    """
    composes email to be sent.
    """
    # Login user and recipients
    recipients = ', '.join(params['resp']) if type(params['resp']) == list else params['resp']

    msg = MIMEMultipart()
    msg['From'] = "Budget with M.E."
    msg['To'] = recipients
    msg['Subject'] = f"Budget with M.E. as of {today}"

    with open(params['content'], 'r') as f:
        msg.attach(MIMEText(f.read(), 'html'))

    with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(params['email_user'], params['email_pw'])
        server.sendmail(
            params['email_user'], params['resp'], msg.as_string()
        )
    print(f'[E-mail] <{t_stamp}>: Sending Email, TLS')

def highlights(s, budget, remaining):
    is_red = pd.Series(data=False, index=s.index)
    if s.loc[remaining]/s.loc[budget] < 0:
        color = 'rgb(222, 37, 37)'
    elif s.loc[remaining]/s.loc[budget] < 0.25:
        color = 'lightcoral'
    elif s.loc[remaining]/s.loc[budget] < 0.5:
        color = 'lightgoldenyellow'
    elif s.loc[remaining]/s.loc[budget] < 0.75:
        color = 'rgb(237, 184, 87)'
    else:
        color = 'rgb(65, 206, 74)'
    return [f'background-color: {color}' for v in is_red]

def main():

    today = dt.now().strftime("%m/%d/%Y %I:%M%p")
    t_stamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")

    parameters_json = open("main/parameters.json")
    json_ = "main/budgetwithme.json"
    params = json.load(parameters_json)

    url = "https://docs.google.com/spreadsheets/d/{0}/edit?usp=sharing".format(params['sheet_id'])

    print(f'[Data] <{t_stamp}>: Composing data to be sent.')

    budget_ws = get_gsheets(url, 'Summary', json_, t_stamp)
    budget = pd.DataFrame(budget_ws.get("B3:D7"))
    budget.columns = ['Category', 'Budget', 'Remaining']
    budget['Budget'] = budget['Budget'].str.replace("$", "", regex=False).str\
        .replace(",", "", regex=False).astype(float)
    budget['Remaining'] = budget['Remaining'].str.replace("$", "", regex=False).str\
        .replace(",", "", regex=False).astype(float)
    
    header_style = {'selector': 'th', 'props': [('background-color','lightcyan')]}

    df_budget = budget.iloc[2:,:].reset_index(drop=True)
    df_budget_html = df_budget.style.format("${0}",precision=2, subset = ["Budget", "Remaining"]).hide(axis="index")\
        .set_table_styles([header_style]).apply(highlights, budget="Budget",remaining="Remaining", axis=1).to_html()

    df_essentials = budget.iloc[:2,:].reset_index(drop=True)
    df_essentials_html = df_essentials.style.format("${0}",precision=2, subset = ["Budget", "Remaining"]).hide(axis="index")\
        .set_table_styles([header_style]).apply(highlights, budget="Budget",remaining="Remaining", axis=1).to_html()

    cat_ws = get_gsheets(url, 'Budget & Investments', json_, t_stamp)
    categories = pd.DataFrame(cat_ws.get("E3:E25"))
    categories = categories.iloc[:][0]

    expenses_ws = get_gsheets(url, 'Expenses Tracker', json_, t_stamp)
    expenses = pd.DataFrame(expenses_ws.get("E6:J800"))
    new_header = expenses.iloc[0]
    expenses = expenses.iloc[1:]
    expenses.columns = new_header
    expenses['Amount'] = expenses['Amount'].str.replace("$", "", regex=False).\
            str.replace(",", "", regex=False).astype(float) * -1
    
    weekly_summary = expenses.loc[(expenses['Date'].isin(current_week()) & expenses['Category'].isin(categories)),['Category','Amount', 'Date']]
    weekly_summary = weekly_summary.groupby('Category').sum('Amount').reset_index()    
    weekly_summary.columns = ['Category','Weekly Total']
    weekly_summary_html = weekly_summary.style.format("${0}",precision=2, subset = ["Weekly Total"]).hide(axis="index")\
        .set_table_styles([header_style, {'selector': 'td', 'props': [('background-color','lightcyan')]}]).to_html()


    credit_card_dues = pd.DataFrame(expenses_ws.get("L2:N3"))
    credit_card_dues[2] = credit_card_dues[2].str.replace("$", "", regex=False).\
            str.replace(",", "", regex=False).astype(float)
    cc_dues_html = credit_card_dues.style.format("${0}",precision=2, subset=[2]).hide(axis="columns").hide(axis="index")\
        .set_table_styles([header_style, {'selector': 'td', 'props': [('background-color','lightcyan')]}]).to_html()

    #Creates the budget content
    create_budget_body(df_budget_html, df_essentials_html, weekly_summary_html, cc_dues_html, t_stamp, params['content'])

    #send_mail(params, today, t_stamp)

if __name__ == '__main__':
    main()
