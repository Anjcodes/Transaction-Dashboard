import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def main():
    st.set_page_config(page_title="Transaction Dashboard", page_icon=":bar_chart:", layout="wide")
    st.title(" :bar_chart: Transaction Dashboard")
    st.write(
        """
        This app provides an in-depth analysis of customer transactions. 
        It allows you to filter data by customizable age groups, gender, and other relevant demographics.
        You can clean your data, merge transaction data with customer demographics from separate sheets,
        and gain insights into transaction patterns for data-driven decision-making.
        """
    )
    st.markdown('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)

    merged_data = None

    # Allow user to upload data
    f1 = st.file_uploader(":file_folder: Upload a file", type=["csv", "txt", "xlsx", "xls"])

    if f1 is not None:
        try:
            # Automatically read Excel or CSV files
            if f1.name.endswith(".xlsx") or f1.name.endswith(".xls"):
                # Load all sheets and let user decide whether to merge
                xls = pd.ExcelFile(f1)
                sheet_names = xls.sheet_names
                if len(sheet_names) > 1:
                    st.sidebar.subheader("Multiple Sheets Detected")
                    merge_sheets = st.sidebar.checkbox("Merge sheets?", value=True)
                    if merge_sheets:
                        transaction_sheet = st.sidebar.selectbox("Select Transaction Sheet", sheet_names)
                        demographic_sheet = st.sidebar.selectbox("Select Demographic Sheet", sheet_names)
                        transactions = pd.read_excel(f1, sheet_name=transaction_sheet)
                        customer_demographics = pd.read_excel(f1, sheet_name=demographic_sheet)
                        # Merge based on common column if exists
                        common_columns = set(transactions.columns) & set(customer_demographics.columns)
                        #st.write(common_columns)
                        if common_columns:
                            common_column = st.sidebar.selectbox("Select Common Column to Merge", list(common_columns))
                            merged_data = pd.merge(transactions, customer_demographics, on=common_column, how="left")
                        else:
                            st.error("No common columns found to merge datasets.")
                            st.stop()
                    else:
                        selected_sheet = st.sidebar.selectbox("Select Sheet to Use", sheet_names)
                        merged_data = pd.read_excel(f1, sheet_name=selected_sheet)
                else:
                    # If only one sheet, load it directly
                    merged_data = pd.read_excel(f1, sheet_name=sheet_names[0])
            else:
                merged_data = pd.read_csv(f1)

            # Dynamically ask for columns to use based on dataset content
            available_columns = merged_data.columns
            st.sidebar.subheader("Select Columns for Dashboard")
            date_column = st.sidebar.selectbox("Select Transaction Date Column", ["None"] + list(available_columns))
            list_price_column = st.sidebar.selectbox("Select Transaction Amount Column", ["None"] + list(available_columns))
            gender_column = st.sidebar.selectbox("Select Gender Column", ["None"] + list(available_columns))
            age_column = st.sidebar.selectbox("Select Age Column", ["None"] + list(available_columns))
            other_filter_column = st.sidebar.selectbox("Select Other Filter Column", ["None"] + list(available_columns))
            currency = st.sidebar.selectbox("Select Currency", ["$", "€", "₦", "£", "¥", "₹", "₩", "₽", "₪", "CHF", "A$", "C$", "HK$", "NZ$", "د.إ", "R$", "₺", "₴", "฿", "S$"])

            # Data Cleaning Options
            st.sidebar.subheader("Data Cleaning Options")
            if gender_column != "None":
                unique_genders = list(merged_data[gender_column].unique())
                selected_gender_values = st.sidebar.multiselect(f"Select Gender Values to Keep (Others will be 'Other')", unique_genders, default=unique_genders)
                merged_data[gender_column] = merged_data[gender_column].apply(lambda x: x if x in selected_gender_values else "Other")
                merged_data[gender_column].fillna("Other", inplace=True)
            
            if age_column != "None":
                merged_data[age_column].fillna(merged_data[age_column].median(), inplace=True)
            
            if other_filter_column != "None":
                unique_segments = list(merged_data[other_filter_column].unique())
                selected_filter = st.sidebar.multiselect(f"Select Segment Values to Keep (Others will be 'Other')", unique_segments, default=unique_segments)
                merged_data[other_filter_column] = merged_data[other_filter_column].apply(lambda x: x if x in selected_filter else "Other")
                merged_data[other_filter_column].fillna("Other", inplace=True)

            
        # Age grouping if an age column is selected
            if age_column != "None":
                bins = st.sidebar.text_input("Define Age Bins (comma-separated)", "0, 11, 27, 43, 59, 78, 100")
                labels = st.sidebar.text_input("Define Age Labels (comma-separated)", "Gen Alpha, Gen Z, Millennials, Gen X, Baby Boomers, Silent Gen")
                try:
                    bins = list(map(float, bins.split(",")))
                    labels = labels.split(",")
                    
                    # Creating age group column in merged_data
                    merged_data['age_group'] = pd.cut(merged_data[age_column], bins=bins, labels=labels, right=False, include_lowest=True)
                    unique_age_groups = ["All"] + list(merged_data['age_group'].dropna().unique())
                    
                    st.sidebar.subheader("Filter Data")
                    selected_age_group = st.sidebar.selectbox("Select Age Group", unique_age_groups)
                    
                    # Filtering data based on age group selection after age_group column is created
                    if selected_age_group != "All":
                        filtered_data = merged_data[merged_data['age_group'] == selected_age_group]
                    else:
                        filtered_data = merged_data
                except ValueError:
                    st.error("Please enter valid numeric bins and labels.")
            else:
                filtered_data = merged_data

            # Filter by gender and wealth segment if selected
            if gender_column != "None":
                unique_genders = ["All"] + list(merged_data[gender_column].unique())
                selected_gender = st.sidebar.selectbox("Select Gender", unique_genders)
                if selected_gender != "All":
                    filtered_data = merged_data[merged_data[gender_column] == selected_gender]
            
            if other_filter_column != "None":
                unique_other_filter = ["All"] + list(merged_data[other_filter_column].unique())
                selected_other_filter = st.sidebar.selectbox("Select for Other Filter", unique_other_filter)
                if selected_other_filter != "All":
                    filtered_data = merged_data[merged_data[other_filter_column] == selected_other_filter]

            # Date filter if a date column is selected
            if date_column != "None":
                with st.subheader("Date Filter"):
                    merged_data[date_column] = pd.to_datetime(merged_data[date_column], errors="coerce")
                    merged_data.dropna(subset=[date_column], inplace=True)
                    min_date, max_date = merged_data[date_column].min().date(), merged_data[date_column].max().date()
                    
                    # Create two columns for date input
                    col1, col2 = st.columns(2)
                    with col1:
                        date1 = st.sidebar.date_input("Start Date", min_date)
                    with col2:
                        date2 = st.sidebar.date_input("End Date", max_date)

                    # Filter the data based on selected dates
                    filtered_data = merged_data[(merged_data[date_column] >= pd.to_datetime(date1)) & (merged_data[date_column] <= pd.to_datetime(date2))]
            
        
                


            if 'filtered_data' in locals() and not filtered_data.empty:
                # Convert transaction date to datetime and extract year-month for grouping if needed
                if date_column != "None":
                    filtered_data[date_column] = pd.to_datetime(filtered_data[date_column])
                    filtered_data['Month'] = filtered_data[date_column].dt.to_period("M").astype(str)

                # Display charts with columns for alignment
                col1, col2 = st.columns(2)
                
                # Calculate and display summary metrics
                if list_price_column != "None":
                    total_transactions = len(filtered_data)
                    total_amount = filtered_data[list_price_column].sum()
                    
                    # Create a card layout using Markdown and HTML/CSS
                    with col1:
                        st.markdown(
                            f"""
                            <div style="background-color: rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 20px; text-align: center;">
                                <h4 style="color: white;">Total Transactions</h4>
                                <h2 style="color: white;">{total_transactions}</h2>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                    st.write(" ")

                    with col2:
                        st.markdown(
                            f"""
                            <div style="background-color: rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 20px; text-align: center;">
                                <h4 style="color: white;">Total Transaction Amount</h4>
                                <h2 style="color: white;">{currency}{total_amount:,.2f}</h2>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )


                st.write("")  # Add space between charts
                

                # Chart 1: Bar Chart - Transaction Amount by Month
                if list_price_column != "None" and date_column != "None":              
                        st.subheader("Transaction Amount by Month")
                        monthly_data = filtered_data.groupby('Month')[list_price_column].sum().reset_index()
                        fig_bar = px.bar(monthly_data, x='Month', y=list_price_column, title="", color=list_price_column)
                        st.plotly_chart(fig_bar)
                
                st.write("")  # Add space between charts

                # Display charts with columns for alignment
                col1, col2 = st.columns(2)
                
                # Pie Chart: Distribution by Gender or Selected Filter
                if gender_column != "None":
                    with col1:
                        st.subheader("Distribution by Gender")
                        pie_chart = px.pie(
                            filtered_data, names=gender_column,
                            title="",
                            hole=0.4
                        )
                        st.plotly_chart(pie_chart, use_container_width=True)

                st.write("  ")  # Add space between charts

                # Bar Chart: Total Amount per Selected Other Filter (e.g., Gender, Age Group)
                if other_filter_column != "None" and list_price_column != "None":
                    with col2:
                        st.subheader("Total Amount by " + other_filter_column)
                        bar_chart = px.bar(
                            filtered_data.groupby(other_filter_column)[list_price_column].sum().reset_index(),
                            x=other_filter_column, y=list_price_column,
                            title=f"",
                            labels={list_price_column: "Total Amount"}
                        )
                        st.plotly_chart(bar_chart, use_container_width=True)
                
                # Time Series: Total Amount Over Time
                    if date_column != "None" and list_price_column != "None":
                            st.subheader("Time Series of Total Amount")
                            time_series = px.line(
                                filtered_data.groupby(date_column)[list_price_column].sum().reset_index(),
                                x=date_column, y=list_price_column,
                                title="",
                                labels={list_price_column: "Total Amount"}
                            )
                            st.plotly_chart(time_series, use_container_width=True) 
                
                # Display charts with columns for alignment
                col1, col2 = st.columns(2)

                # Bar Chart: Transaction Amount by Age Group if age grouping is done
                if age_column != "None" and list_price_column != "None" and 'age_group' in filtered_data.columns:
                    with col1:
                        st.subheader("Total Transaction by Age Group")
                        # Aggregating transaction amount by age group
                        age_group_summary = filtered_data.groupby('age_group')[list_price_column].sum().reset_index()
                        
                        # Creating horizontal bar chart
                        bar_chart = px.bar(
                            age_group_summary, x=list_price_column, y='age_group',
                            title="",
                            labels={'age_group': "Age Group", list_price_column: "Total Transaction Amount"},
                            orientation='h'  # Set orientation to horizontal
                        )
                        st.plotly_chart(bar_chart, use_container_width=True)
                    
                # Treemap: Total Amount by Other Filter and Gender (or any available dimensions)
                    if other_filter_column != "None" and gender_column != "None" and list_price_column != "None":
                        with col2:
                            st.subheader("Treemap of Total Amount by " + other_filter_column + " and Gender")
                            treemap = px.treemap(
                                filtered_data, path=[other_filter_column, gender_column],
                                values=list_price_column, title="")
                            st.plotly_chart(treemap, use_container_width=True)

                    # Histogram: Transaction Amount Distribution
                    if list_price_column != "None":
                            st.subheader("Transaction Amount Distribution")
                            histogram = px.histogram(
                                filtered_data, x=list_price_column,
                                title="",
                                labels={list_price_column: "Amount"}
                            )
                            st.plotly_chart(histogram, use_container_width=True)    
            else:
                st.warning("No data available to display other charts. Please select columns and filter your data.")
            


            # Display the filtered data
            st.write("Filtered Data")
            st.dataframe(merged_data)

            

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.info("Please upload a file to begin analysis.")


if __name__ == "__main__":
    main()