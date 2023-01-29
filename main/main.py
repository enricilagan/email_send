import pandas as pd
import gspread as gs
import json
from datetime import datetime as dt
from utils.email_creator import create_budget_body, send_mail
from utils.timehelper import current_week

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

def create_df_html(url, worksheet, json_, t_stamp):

    header_style = {'selector': 'th', 'props': [('background-color','lightcyan')]}

    gc = gs.service_account(filename=json_)
    sh = gc.open_by_url(url)
    cat_ws = sh.worksheet('Budget & Investments')
    categories = pd.DataFrame(cat_ws.get("E3:E25"))
    categories = categories.iloc[:][0]

    print("[Data] <{0}>: Getting data from google sheets, {1}".format(t_stamp, worksheet))
    gc = gs.service_account(filename=json_)
    sh = gc.open_by_url(url)
    ws = sh.worksheet(worksheet)

    if worksheet == 'Summary':
        df = pd.DataFrame(ws.get("B3:D7"))
        df.columns = ['Category', 'Budget', 'Remaining']
        df['Budget'] = df['Budget'].str.replace("$", "", regex=False).str\
            .replace(",", "", regex=False).astype(float)
        df['Remaining'] = df['Remaining'].str.replace("$", "", regex=False).str\
            .replace(",", "", regex=False).astype(float)

        df_budget = df.iloc[2:,:].reset_index(drop=True)
        df_budget_html = df_budget.style.format("${0}",precision=2, subset = ["Budget", "Remaining"]).hide(axis="index")\
            .set_table_styles([header_style]).apply(highlights, budget="Budget",remaining="Remaining", axis=1).to_html()

        df_essentials = df.iloc[:2,:].reset_index(drop=True)
        df_essentials_html = df_essentials.style.format("${0}",precision=2, subset = ["Budget", "Remaining"]).hide(axis="index")\
            .set_table_styles([header_style]).apply(highlights, budget="Budget",remaining="Remaining", axis=1).to_html()

        return df_budget_html, df_essentials_html

    if worksheet == 'Expenses Tracker':

        df = pd.DataFrame(ws.get("E6:J800"))
        new_header = df.iloc[0]
        df = df.iloc[1:]
        df.columns = new_header
        df['Amount'] = df['Amount'].str.replace("$", "", regex=False).\
                str.replace(",", "", regex=False).astype(float) * -1
        
        weekly_summary = df.loc[(df['Date'].isin(current_week()) & df['Category'].isin(categories)),['Category','Amount', 'Date']]
        weekly_summary = weekly_summary.groupby('Category').sum('Amount').reset_index()    
        weekly_summary.columns = ['Category','Weekly Total']
        weekly_summary_html = weekly_summary.style.format("${0}",precision=2, subset = ["Weekly Total"]).hide(axis="index")\
            .set_table_styles([header_style, {'selector': 'td', 'props': [('background-color','lightcyan')]}]).to_html()

        df2 = pd.DataFrame(ws.get("L2:N3"))
        df2[2] = df2[2].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float)
        cc_dues_html = df2.style.format("${0}",precision=2, subset=[2]).hide(axis="columns").hide(axis="index")\
        .set_table_styles([header_style, {'selector': 'td', 'props': [('background-color','lightcyan')]}]).to_html()

        return weekly_summary_html, cc_dues_html

def main():

    today = dt.now().strftime("%m/%d/%Y %I:%M%p")
    t_stamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")

    parameters_json = open(".creds/parameters.json")
    json_ = ".creds/budgetwithme.json"
    params = json.load(parameters_json)

    url = "https://docs.google.com/spreadsheets/d/{0}/edit?usp=sharing".format(params['sheet_id'])

    print(f'[Data] <{t_stamp}>: Composing data to be sent.')

    df_budget_html, df_essentials_html = create_df_html(url, 'Summary', json_, t_stamp)
    df_weekly_html, cc_dues_html = create_df_html(url, 'Expenses Tracker', json_, t_stamp)

    #Creates the budget content
    create_budget_body(df_budget_html, df_essentials_html, df_weekly_html, cc_dues_html, t_stamp, params['content'])
    send_mail(params, today, t_stamp)

if __name__ == '__main__':
    main()
