import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd


# Create file, separate it from compose email for testing
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