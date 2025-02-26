import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import numpy as np
import locale

# Set locale for Indian formatting
locale.setlocale(locale.LC_ALL, 'en_IN')

# Configure Streamlit page
st.set_page_config(page_title='HDFC Bank Statement Analysis', page_icon=':moneybag:')

# Display title and description
st.title('Visualize Your HDFC Bank Statement')
st.write('Export your HDFC Bank statement as a XLS file and drop it here to analyze your expenses')
st.markdown("*Note: We don't store your data*")

# Sample statement URLs
sample_statements = [
    "https://github.com/myselfshravan/Python/files/10087176/statement23.xls",
    "https://github.com/myselfshravan/Streamlit-Apps-Python/files/11287111/Acct.Statement_2022_Full.xls"
]

# Allow user to choose between sample data and file upload
agree = st.checkbox('Use Sample Statement')
if agree:
    uploaded_file = st.selectbox('Select Sample Statement', sample_statements)
else:
    uploaded_file = st.file_uploader("Choose a xls formatted file of HDFC Bank Statement", type="xls")


@st.cache_data
def load_data(file):
    """
    Loads and preprocesses the HDFC Bank statement Excel file.

    Parameters:
        file: File path or uploaded file object.

    Returns:
        DataFrame: Raw data extracted from the Excel file.
    """
    # Read Excel file and remove header/footer rows (adjust indices as necessary)
    df = pd.read_excel(file, sheet_name=0)
    df = df.iloc[21:-18]

    # Drop unwanted columns and rows
    df = df.drop(df.columns[[0, 2]], axis=1)
    df = df.drop(df.index[1])
    df = df.fillna(0)

    # Rename columns for consistency
    df.rename(
        columns={
            'Unnamed: 1': 'Narration',
            'Unnamed: 3': 'Date',
            'Unnamed: 4': 'Withdrawal',
            'Unnamed: 5': 'Deposited',
            'Unnamed: 6': 'Balance'
        },
        inplace=True
    )
    return df


def extract_upi_name(upi_string):
    """
    Extracts the UPI name from a given transaction string.

    Parameters:
        upi_string (str): Transaction description.

    Returns:
        str or np.nan: Extracted UPI name.
    """
    if upi_string.startswith("UPI-"):
        return upi_string.split('-')[1] if '-' in upi_string else np.nan
    elif upi_string.startswith("POS"):
        parts = upi_string.split(" ")
        return parts[2] if len(parts) > 2 else np.nan
    elif "RTGS" in upi_string or "NEFT" in upi_string:
        parts = upi_string.split('-')
        return parts[2] if len(parts) > 2 else np.nan
    elif upi_string.startswith("CASH DEPOSIT BY"):
        parts = upi_string.split('-')
        return parts[1].strip() if len(parts) > 1 else np.nan
    else:
        return np.nan


def extract_upi_description(upi_string):
    """
    Extracts the UPI transaction description from a given string.

    Parameters:
        upi_string (str): Transaction description.

    Returns:
        str or np.nan: Extracted description.
    """
    if upi_string.startswith("POS"):
        parts = upi_string.split(" ")
        return " ".join(parts[2:]) if len(parts) > 2 else np.nan
    elif "RTGS" in upi_string or "NEFT" in upi_string:
        parts = upi_string.split('-')
        return parts[-2] if len(parts) > 2 else parts[-1]
    elif upi_string.startswith("CASH DEPOSIT BY"):
        parts = upi_string.split('-')
        return parts[-1].strip() if len(parts) > 2 else np.nan
    else:
        return upi_string.split('-')[-1]


def preprocess_data(df):
    """
    Processes the raw DataFrame:
      - Converts date columns.
      - Converts numeric columns safely.
      - Extracts UPI details.
      - Computes cumulative sums.

    Parameters:
        df (DataFrame): Raw bank statement data.

    Returns:
        DataFrame: Preprocessed data.
    """
    # Convert Date column to datetime and create formatted date column
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y', errors='coerce')
    df['Date_Formated'] = df['Date'].dt.strftime('%d-%b-%Y')

    # Convert numeric columns using pandas to_numeric for safety
    df['Withdrawal'] = pd.to_numeric(df['Withdrawal'], errors='coerce').fillna(0)
    df['Deposited'] = pd.to_numeric(df['Deposited'], errors='coerce').fillna(0)
    df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce').fillna(0)

    # Ensure Narration is a string
    df['Narration'] = df['Narration'].astype(str)

    # Extract UPI details from the Narration
    df['UPIs'] = df['Narration'].str.split('@').str[0]
    df['UPI_Name'] = df['UPIs'].apply(extract_upi_name)
    df['UPI_Bank'] = df['Narration'].str.extract(r'@(.*?)-')
    df['UPI_Description'] = df['Narration'].apply(extract_upi_description)

    # Reset the index to start from 1 for display purposes
    df.index = range(1, len(df) + 1)

    # Compute cumulative sums for withdrawal and deposited amounts
    df['Cumulative_Withdrawal'] = df['Withdrawal'].cumsum()
    df['Cumulative_Deposited'] = df['Deposited'].cumsum()

    return df


def display_metrics(df):
    """
    Displays key metrics from the bank statement.

    Parameters:
        df (DataFrame): Preprocessed bank statement data.
    """
    start_date = df['Date'].iloc[0]
    end_date = df['Date'].iloc[-1]
    days = (end_date - start_date).days

    st.markdown(f"**Statement Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    st.markdown(f"**Number of Days:** {days}")

    total_withdrawal = df['Withdrawal'].sum()
    total_deposit = df['Deposited'].sum()

    st.markdown(f"**Total Withdrawal and Deposit:** Rs {total_withdrawal:.2f} - Rs {total_deposit:.2f}")
    st.markdown(f"**Opening and Closing Balance:** Rs {df['Balance'].iloc[0]} and Rs {df['Balance'].iloc[-1]}")
    st.markdown(f"**Total Transactions:** {len(df)}")

    if days > 0:
        st.markdown(f"**Average Withdrawal per Day:** Rs {(total_withdrawal / days):.2f}")
        st.markdown(f"**Average Withdrawal per Month:** Rs {(total_withdrawal / (days / 30)):.2f}")


def display_charts(df):
    """
    Renders balance and transaction trend charts.

    Parameters:
        df (DataFrame): Preprocessed bank statement data.
    """
    # Balance trend chart using Streamlit's built-in line_chart
    balance_trend = pd.DataFrame({'Balance': df['Balance']}, index=df['Date'])
    st.subheader('Balance Trend')
    st.line_chart(balance_trend, use_container_width=True)

    # Radio button for transaction type selection
    transaction_type = st.radio('Select Transaction Type', ('Withdrawal', 'Deposited'))

    if transaction_type == 'Withdrawal':
        trend_data = pd.DataFrame({'Withdrawal': df['Cumulative_Withdrawal']}, index=df['Date'])
        st.subheader('Withdrawal Trend')
        st.line_chart(trend_data, use_container_width=True)
        fig_bar = px.bar(df, x='Date', y='Withdrawal', title='Withdrawals')
        st.plotly_chart(fig_bar, use_container_width=True)
        fig_scatter = px.scatter(df, x='Date', y='Withdrawal', color='UPI_Name', title='Withdrawal Details')
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        trend_data = pd.DataFrame({'Deposited': df['Cumulative_Deposited']}, index=df['Date'])
        st.subheader('Deposit Trend')
        st.line_chart(trend_data, use_container_width=True)
        fig_bar = px.bar(df, x='Date', y='Deposited', title='Deposits')
        st.plotly_chart(fig_bar, use_container_width=True)
        fig_scatter = px.scatter(df, x='Date', y='Deposited', color='UPI_Name', title='Deposit Details')
        st.plotly_chart(fig_scatter, use_container_width=True)


def filter_by_date(df):
    """
    Provides multiple filtering options (by specific date, by month/year, and by date range)
    and displays filtered results.

    Parameters:
        df (DataFrame): Preprocessed bank statement data.
    """
    # ----- Filter by a Specific Date -----
    st.subheader("Filter by Date")
    default_date = df['Date'].iloc[0].date()
    selected_date = st.date_input('Select Date', value=default_date)
    selected_day = df[df['Date'].dt.date == selected_date]
    st.dataframe(
        selected_day[['UPI_Name', 'UPI_Description', 'Withdrawal', 'Deposited', 'Balance', 'Narration']],
        use_container_width=True
    )
    total_day_withdrawal = locale.format_string('%d', selected_day['Withdrawal'].sum(), grouping=True)
    total_day_deposited = locale.format_string('%d', selected_day['Deposited'].sum(), grouping=True)
    st.markdown(
        f"**Total Withdrawals on {selected_date.strftime('%d %B')}:** <span style='color:red;'>Rs {total_day_withdrawal}</span>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"**Total Deposits on {selected_date.strftime('%d %B')}:** <span style='color:green;'>Rs {total_day_deposited}</span>",
        unsafe_allow_html=True
    )

    # ----- Filter by Month and Year -----
    st.subheader("Filter by Month and Year")
    df['Month'] = df['Date'].dt.strftime('%B')
    df['Year'] = df['Date'].dt.strftime('%Y')
    selected_month = st.selectbox('Select Month', df['Month'].unique())
    selected_year = st.selectbox('Select Year', df['Year'].unique())
    filtered_month = df[(df['Month'] == selected_month) & (df['Year'] == selected_year)]
    st.dataframe(
        filtered_month[['UPI_Name', 'UPI_Description', 'Date_Formated', 'Withdrawal', 'Deposited', 'Balance']],
        use_container_width=True
    )
    total_month_withdrawal = locale.format_string('%d', filtered_month['Withdrawal'].sum(), grouping=True)
    total_month_deposited = locale.format_string('%d', filtered_month['Deposited'].sum(), grouping=True)
    st.markdown(
        f"**Total Withdrawals in {selected_month} {selected_year}:** <span style='color:red;'>Rs {total_month_withdrawal}</span>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"**Total Deposits in {selected_month} {selected_year}:** <span style='color:green;'>Rs {total_month_deposited}</span>",
        unsafe_allow_html=True
    )

    # ----- Filter by a Date Range -----
    st.subheader("Filter by Date Range")
    start_range = df['Date'].min().date()
    end_range = df['Date'].max().date()
    start_date = st.date_input('Start Date', value=start_range, key='range_start')
    end_date = st.date_input('End Date', value=end_range, key='range_end')
    if start_date and end_date:
        mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
        range_df = df.loc[mask]
        st.dataframe(
            range_df[['UPI_Name', 'UPI_Description', 'Date_Formated', 'Withdrawal', 'Deposited', 'Balance']],
            use_container_width=True
        )
        total_range_withdrawal = locale.format_string('%d', range_df['Withdrawal'].sum(), grouping=True)
        total_range_deposited = locale.format_string('%d', range_df['Deposited'].sum(), grouping=True)
        st.markdown(
            f"**Total Withdrawal in Date Range:** <span style='color:red;'>Rs {total_range_withdrawal}</span>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"**Total Deposited in Date Range:** <span style='color:green;'>Rs {total_range_deposited}</span>",
            unsafe_allow_html=True
        )


def display_additional_insights(df):
    """
    Displays extra insights including UPI-wise total withdrawal,
    the highest single transaction, and the day with the highest spending.

    Parameters:
        df (DataFrame): Preprocessed bank statement data.
    """
    st.subheader('Total Amount Spent on Each UPI')
    upi_group = df.groupby('UPIs')['Withdrawal'].sum().sort_values(ascending=False)
    st.dataframe(upi_group, use_container_width=True)

    st.subheader('Highest Amount Spent in One Transaction')
    if not df.empty and df['Withdrawal'].max() > 0:
        highest_transaction = df.loc[df['Withdrawal'].idxmax()]
        st.dataframe(highest_transaction.to_frame().T, use_container_width=True)

    daily_withdrawal = df.groupby("Date")['Withdrawal'].sum()
    if not daily_withdrawal.empty:
        max_day = daily_withdrawal.idxmax()
        max_amount = daily_withdrawal.max()
        st.subheader('Highest Spending in a Day')
        st.write(f"On {max_day.strftime('%d %B %Y')}: Rs {max_amount:.2f}")


# Main execution block
if uploaded_file is not None:
    try:
        # Load raw data from the uploaded file or sample URL
        raw_df = load_data(uploaded_file)
        # Preprocess the data (convert types, extract details, compute cumulative sums)
        processed_df = preprocess_data(raw_df)

        # Display overall metrics
        display_metrics(processed_df)

        # Show balance and transaction trend charts
        display_charts(processed_df)

        # Provide filtering options and display filtered data
        filter_by_date(processed_df)

        # Display additional insights
        display_additional_insights(processed_df)

    except Exception as e:
        st.error(f"Error processing file: {e}")
