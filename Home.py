import streamlit as st
import pandas as pd
from datetime import date, datetime
import plotly.express as px

st.set_page_config(page_title='HDFC Bank Statement Analysis', page_icon=':moneybag:')

st.title('Visualize Your HDFC Bank Statement')
st.write('Export your HDFC Bank statement as a XLS file and drop it here to analyze your expenses')
st.markdown("*Note: We don't store your data*")

sample_statements = ["https://github.com/myselfshravan/Python/files/10087176/statement23.xls",
                     "https://github.com/myselfshravan/Streamlit-Apps-Python/files/11287111/Acct.Statement_2022_Full.xls"]
agree = st.checkbox('Use Sample Statement')
if agree:
    uploaded_file = st.selectbox('Select Sample Statement', sample_statements)
else:
    uploaded_file = st.file_uploader("Choose a xls formate file of HDFC Bank Statement", type="xls")

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        df = df.iloc[21:-18]
        df = df.drop(df.columns[[0, 2]], axis=1)
        df = df.drop(df.index[1])
        df = df.fillna(0)
        df.rename(
            columns={'Unnamed: 1': 'UPIs', 'Unnamed: 3': 'Date', 'Unnamed: 4': 'Withdrawal', 'Unnamed: 5': 'Deposited',
                     'Unnamed: 6': 'Balance'},
            inplace=True)

        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y').dt.date
        df['Withdrawal'] = df['Withdrawal'].apply(lambda x: "{:.1f}".format(x)).astype(float)
        df['Deposited'] = df['Deposited'].apply(lambda x: "{:.1f}".format(x)).astype(float)
        df['Balance'] = df['Balance'].astype(float)
        df['UPIs'] = df['UPIs'].astype(str)
        df['UPIs'] = df['UPIs'].str.split('@', expand=True)[0]
        df['UPIs'] = df['UPIs'].str.split('-', expand=True)[1]
        df.index = range(1, len(df) + 1)

        start_date = df['Date'].iloc[0].strftime("%B %d %Y")
        end_date = df['Date'].iloc[-1].strftime("%B %d %Y")

        start = datetime.strptime(df['Date'].iloc[0].strftime('%d/%m/%y'), '%d/%m/%y')
        end = datetime.strptime(df['Date'].iloc[-1].strftime('%d/%m/%y'), '%d/%m/%y')
        st.write(f"Statement Period: {start_date} to {end_date}")
        days = (end - start).days
        st.write(f"Number of Days: {days}")
        total_withdrawal = df['Withdrawal'].sum()
        total_deposit = df['Deposited'].sum()
        st.write(f"Total Withdrawal and Deposit: Rs {total_withdrawal} - Rs {total_deposit}")
        st.write(f"Closing and Opening Balance: {df['Balance'].iloc[0]} and {df['Balance'].iloc[-1]}")
        st.write(f"Total Transactions: {len(df)}")
        st.write(f"Average Withdrawal per day: {(total_withdrawal / days):.2f}")
        st.write(f"Average Withdrawal per month: {total_withdrawal / (days / 30):.2f}")
        time_frame = list(df['Date'])
        withdrawal = list(df['Withdrawal'])
        for i in range(1, len(withdrawal)):
            withdrawal[i] = withdrawal[i] + withdrawal[i - 1]
        deposited = list(df['Deposited'])
        for i in range(1, len(deposited)):
            deposited[i] = deposited[i] + deposited[i - 1]

        balance = list(df['Balance'])
        line = pd.DataFrame({'Balance': balance}, index=time_frame)
        st.subheader('Balance Trend')
        st.line_chart(line, use_container_width=True)

        # fig = px.line(df, x='Date', y='Balance', title='Balance Trend', color_discrete_sequence=['#1f77b4'],
        #               template='plotly_white', labels={'Date': 'Date', 'Balance': 'Balance'},
        #               hover_data={'Date': False, 'Balance': ':.2f'})
        # st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)

        val = st.radio('Select', ('Withdrawal', 'Deposited'))
        if val == 'Withdrawal':
            withdraw_line = pd.DataFrame({'Withdrawal': withdrawal}, index=time_frame)
            st.subheader('Withdrawal Trend')
            st.line_chart(withdraw_line, use_container_width=True)
            fig = px.bar(df, x='Date', y='Withdrawal', title='Withdrawals')
            st.plotly_chart(fig, use_container_width=True)
            figs = px.scatter(df, x='Date', y='Withdrawal', color='UPIs', title='Withdrawals')
            st.plotly_chart(figs, use_container_width=True)
        elif val == 'Deposited':
            deposit_line = pd.DataFrame({'Deposited': deposited}, index=time_frame)
            st.subheader('Deposit Trend')
            st.line_chart(deposit_line, use_container_width=True)
            fig = px.bar(df, x='Date', y='Deposited', title='Deposits')
            st.plotly_chart(fig, use_container_width=True)
            figs = px.scatter(df, x='Date', y='Deposited', color='UPIs', title='Deposits')
            st.plotly_chart(figs, use_container_width=True)

        first_date = df['Date'].iloc[0]
        date_selected = st.date_input('Select Date', value=first_date)
        selected = df.loc[df['Date'] == date_selected]
        st.dataframe(selected, use_container_width=True)
        st.write("Total Withdrawals on", date_selected.strftime("%d %B"), "is", selected['Withdrawal'].sum())
        st.write("Total Deposits on", date_selected.strftime("%d %B"), "is", selected['Deposited'].sum())
        df['propdate'] = pd.to_datetime(df['Date'])
        month_selected = st.selectbox('Select Month', df['propdate'].dt.strftime('%B').unique())
        year = st.selectbox('Select Year', df['propdate'].dt.strftime('%Y').unique())
        selected_month = df.loc[
            (df['propdate'].dt.strftime('%B') == month_selected) & (df['propdate'].dt.strftime('%Y') == year)]
        st.dataframe(selected_month, use_container_width=True)
        st.write("Total Withdrawals in", month_selected, "is", selected_month['Withdrawal'].sum())
        st.write("Total Deposits in", month_selected, "is", selected_month['Deposited'].sum())

        st.write("\n")
        st.subheader('Select a date range')
        start_range = df['Date'].iloc[0]
        end_range = df['Date'].iloc[-1]
        start_date = st.date_input('Start date', value=start_range)
        end_date = st.date_input('End date', value=end_range)
        mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
        df = df.loc[mask]
        st.dataframe(df, use_container_width=True)
        st.write(f'Total Deposited: Rs {df["Deposited"].sum()}')
        st.write(f'Total Withdrawal: Rs {df["Withdrawal"].sum()}')

        st.subheader('Total amount spent on each UPI')
        st.dataframe(df.groupby('UPIs')['Withdrawal'].sum().sort_values(ascending=False), use_container_width=True)

        st.subheader('Highest amount spent in one transaction')
        st.dataframe(df.loc[df['Withdrawal'].idxmax()], use_container_width=True)

        in_a_day = df.groupby("Date")['Withdrawal'].sum().sort_values(ascending=False).head(1).index[0].strftime(
            "%d %B")
        st.subheader(f'Highest amount spent in a day')
        amount = df.groupby("Date")['Withdrawal'].sum().sort_values(ascending=False).head(1).values[0]
        st.write(f'On {in_a_day} : Rs {amount}')
    except Exception as ve:
        st.error(f"ValueError: {ve}")
hide_streamlit_style = """
                    <style>
                    # MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    footer:after {
                    content:'Made with passion by Shravan'; 
                    visibility: visible;
    	            display: block;
    	            position: relative;
    	            # background-color: red;
    	            padding: 15px;
    	            top: 2px;
    	            }
                    </style>
                    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
