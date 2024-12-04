import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import pyodbc

# Page configuration
st.set_page_config(page_title="Claim Cost Dashboard", layout="wide")

# Add custom CSS for background and sidebar styling
st.markdown(
    """
    <style>
    body {
        background-color: #f8f9fa;
        color: #343a40;
        font-family: 'Arial', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    [data-testid="stSidebar"] .css-1v3fvcr, .css-1v3fvcr {
        color: #2c3e50 !important;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .metric {
        background-color: #ffffff;
        border: 1px solid #dddddd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Insights", "City Analysis: Lowest Utilization", "City Analysis: Highest Utilization"]
)

# Function to establish the database connection
@st.cache_resource
def get_database_connection():
    return pyodbc.connect(
        'DRIVER={SQL Server};'
        'Server=10.2.60.26\\MSSQLSERVER01;'
        'PORT=1433;'
        'DATABASE=master;'
        'UID=ALX_Administrator;'
        'PWD=B1b9915'
    )

# Function to fetch claim cost data
@st.cache_data
def load_claim_cost_data():
    query = """
    SELECT 
        YEAR(cd.[ProcessDate]) AS Year,
        MONTH(cd.[ProcessDate]) AS Month,
        SUM(cc.[CostGross]) AS TotalClaimCost
    FROM [DatathonDw2024].[dbo].[ClaimsProviderPractice] cp
    INNER JOIN [DatathonDw2024].[dbo].[ClaimCost] cc
        ON cp.[ClaimId] = cc.[ClaimId]
    INNER JOIN [DatathonDw2024].[dbo].[ClaimsDate] cd
        ON cp.[ClaimId] = cd.[ClaimId]
    GROUP BY YEAR(cd.[ProcessDate]), MONTH(cd.[ProcessDate])
    ORDER BY Year, Month;
    """
    cnxn = get_database_connection()
    data = pd.read_sql(query, cnxn)
    data['TotalClaimCost'] = data['TotalClaimCost'].fillna(0)  # Replace null values
    return data

# Function to fetch data for regions with lowest utilization rates
@st.cache_data
def load_lowest_utilization_data():
    query = """
    SELECT TOP (20)
        pp.[PHYS_TOWN] AS Region,
        COUNT(cp.[ClaimId]) AS ClaimCount
    FROM [DatathonDw2024].[dbo].[ClaimsProviderPractice] cp
    INNER JOIN [DatathonDw2024].[dbo].[ProviderPractice] pp
        ON cp.[ProviderPracticeNo] = pp.[PRACTICE_NO]
    GROUP BY pp.[PHYS_TOWN]
    ORDER BY ClaimCount ASC;
    """
    cnxn = get_database_connection()
    data = pd.read_sql(query, cnxn)
    data['ClaimCount'] = data['ClaimCount'].fillna(0)  # Replace null values
    return data

# Function to fetch data for regions with highest utilization rates
@st.cache_data
def load_highest_utilization_data():
    query = """
    SELECT TOP (20)
        pp.[PHYS_TOWN] AS Region,
        COUNT(cp.[ClaimId]) AS ClaimCount
    FROM [DatathonDw2024].[dbo].[ClaimsProviderPractice] cp
    INNER JOIN [DatathonDw2024].[dbo].[ProviderPractice] pp
        ON cp.[ProviderPracticeNo] = pp.[PRACTICE_NO]
    GROUP BY pp.[PHYS_TOWN]
    ORDER BY ClaimCount DESC;
    """
    cnxn = get_database_connection()
    data = pd.read_sql(query, cnxn)
    data['ClaimCount'] = data['ClaimCount'].fillna(0)  # Replace null values
    return data

# Load the data
claim_cost = load_claim_cost_data()
lowest_utilization = load_lowest_utilization_data()
highest_utilization = load_highest_utilization_data()

# Load the data from TOWN.csv.csv for highest utilization
v = pd.read_csv('TOWN.csv.csv')  
#st.write("Data from TOWN.csv.csv", v)  # Display the dataframe for debugging

# Data preprocessing for claim cost data
claim_cost['YearMonth'] = claim_cost['Year'].astype(str) + '-' + claim_cost['Month'].astype(str).str.zfill(2)
claim_cost['YearMonth'] = pd.to_datetime(claim_cost['YearMonth'])

if page == "Overview":
    st.title("📊 Monthly Claim Cost Dashboard")
    st.subheader("Monthly Claim Costs")
    
    # Create the bar chart with larger size and wider bars
    fig, ax = plt.subplots(figsize=(16, 8))  # Larger figure size
    ax.bar(
        claim_cost['YearMonth'], 
        claim_cost['TotalClaimCost'], 
        color='#3498db', 
        edgecolor='black',
        width=10  # Increase width to make bars wider
    )
    
    # Enhance the title, labels, and ticks for better readability
    ax.set_title('Monthly Claim Costs', fontsize=20, weight='bold')
    ax.set_xlabel('Year-Month', fontsize=14)
    ax.set_ylabel('Total Claim Cost', fontsize=14)
    ax.tick_params(axis='x', rotation=45, labelsize=12)  # Rotate and adjust x-tick label size
    ax.tick_params(axis='y', labelsize=12)  # Adjust y-tick label size
    
    # Tight layout for ensuring everything fits well
    plt.tight_layout()
    
    # Display the graph in Streamlit
    st.pyplot(fig)



# Page: Insights
elif page == "Insights":
    st.title("📈 Insights on Monthly Claim Costs")
    if not claim_cost.empty:
        max_cost = claim_cost.loc[claim_cost['TotalClaimCost'].idxmax()]
        min_cost = claim_cost.loc[claim_cost['TotalClaimCost'].idxmin()]
        st.markdown(f"🔵 The highest claim cost occurred in **{max_cost['YearMonth'].strftime('%B %Y')}** with a total of **${max_cost['TotalClaimCost']:,.2f}**.")
        st.markdown(f"🟢 The lowest claim cost occurred in **{min_cost['YearMonth'].strftime('%B %Y')}** with a total of **${min_cost['TotalClaimCost']:,.2f}**.")
        
        st.subheader("Time Series Analysis")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(claim_cost['YearMonth'], claim_cost['TotalClaimCost'], marker='o', color='#1abc9c')
        ax.set_title('Time Series of Monthly Claim Costs', fontsize=16)
        ax.set_xlabel('Year-Month', fontsize=12)
        ax.set_ylabel('Total Claim Cost', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.markdown("⚠️ No data available for insights.")

# Page: City Analysis - Lowest Utilization
elif page == "City Analysis: Lowest Utilization":
    st.title("🏙️ City Analysis: Lowest Utilization Rates")
    st.subheader("Regions with Lowest Utilization Rates")
    st.dataframe(lowest_utilization)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(lowest_utilization['Region'], lowest_utilization['ClaimCount'], color='lightcoral', edgecolor='black')
    ax.set_title('Regions with Lowest Utilization Rates', fontsize=16)
    ax.set_xlabel('Claim Count', fontsize=12)
    ax.set_ylabel('Region', fontsize=12)
    plt.tight_layout()
    st.pyplot(fig)

# Page: City Analysis - Highest Utilization (Using TOWN.csv.csv)
elif page == "City Analysis: Highest Utilization":
    st.title("🏙️ City Analysis: Highest Utilization Rates")
    st.subheader("Regions with Highest Utilization Rates")
    st.dataframe(v)  # Display the dataframe from the CSV

    if 'Region' in v.columns and 'ClaimCount' in v.columns:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.barh(v['Region'], v['ClaimCount'], color='lightgreen', edgecolor='black')
        ax.set_title('Regions with Highest Utilization Rates', fontsize=16)
        ax.set_xlabel('Claim Count', fontsize=12)
        ax.set_ylabel('Region', fontsize=12)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.markdown("⚠️ Data format is incorrect. Ensure the CSV has 'Region' and 'ClaimCount' columns.")
