import streamlit as st
import pandas as pd
import plotly.express as px 
import json 
import os 

st.set_page_config(
    page_title='Simple Expense Tracker App',
    page_icon='🪙',
    layout='wide'
)

#persists between reruns 
if 'categories' not in st.session_state:
    st.session_state.categories = {
        'Uncategorized': [], 
    }

filename='categories.json'

#do the categories exist?
if os.path.exists(filename):
    with open(filename, 'r') as f:
        st.session_state.categories=json.load(f)

def save_categories():
    with open(filename,'w')as f:
        json.dump(st.session_state.categories, f)

def categorize_transactions(df):
    df['Category']='Uncategorized'

    for category, keywords in st.session_state.categories.items():
        if category =='Uncategorized' or not keywords:
            continue

        lowered_keywords = [keyword.lower() for keyword in keywords]

        for idx, row in df.iterrows():
            details=row['Details'].lower().strip()
            if details in lowered_keywords:
                df.at[idx, 'Category'] = category

    return df



def load_transactions(file):
    try: 
        df = pd.read_csv(file)
        df.columns=[col.strip() for col in df.columns]
        df['Amount']= df['Amount'].str.replace(',','').astype(float)
        df['Date']= pd.to_datetime(df['Date'], format='%d %b %Y')

        return categorize_transactions(df)
    except Exception as e:
        st.error(f'Error Processing file: {e}')
        return None

def add_keyword_to_cat(category, keyword):
    keyword=keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False


def main():
    st.title('Simple Expense Dashboard')

    uploaded_file=st.file_uploader('Upload your transcation(s) CSV file', type=['csv','pdf'])

    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            debits_df = df[df['Debit/Credit']== 'Debit'].copy()
            credits_df = df[df['Debit/Credit']== 'Credit'].copy()

            st.session_state.debits_df = debits_df.copy()


            tab1, tab2 = st.tabs(['Expenses (Debits)', 'Payments (Credits)'])
            with tab1:
                new_cat=st.text_input('New category name')
                add_button = st.button('Add category')

                if add_button and new_cat:
                    if new_cat not in st.session_state.categories:
                        st.session_state.categories[new_cat]=[]
                        save_categories()
                        st.rerun()

                st.subheader('Your Expenses')
                edited_df = st.data_editor (
                    st.session_state.debits_df[['Date', 'Details', 'Amount', 'Category']],
                    column_config={
                        'Date': st.column_config.DateColumn(
                            'Date',
                            format='DD/MM/YYYY'
                        ),
                        'Amount': st.column_config.NumberColumn(
                            'Amount',
                            format='%.2f AED'
                        ),
                        'Category': st.column_config.SelectboxColumn(
                            'Category',
                            options=list(st.session_state.categories.keys())
                        )
                    }, 

                    hide_index=True, 
                    use_container_width=True, 
                    key='category_editor',

                )

                save_button = st.button('Apply Changes', type='primary')

                if save_button:
                    for idx, row in edited_df.iterrows():
                        category = row['Category']
                        details = row['Details']

                        # Update the category
                        st.session_state.debits_df.at[idx, 'Category'] = category

                        # Save the transaction detail as a keyword
                        if category != 'Uncategorized':
                            add_keyword_to_cat(category, details)

                    st.success('Changes applied successfully!')

                st.subheader('Expense Summary')
                category_totals = st.session_state.debits_df.groupby('Category')['Amount'].sum().reset_index()
                category_totals = category_totals.sort_values('Amount', ascending=False)

                st.dataframe(
                    category_totals, 
                    column_config={
                     "Amount": st.column_config.NumberColumn("Amount", format="%.2f AED")   
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                fig = px.pie(
                    category_totals,
                    values="Amount",
                    names="Category",
                    title="Expenses by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                st.subheader("Payments Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payments", f"{total_payments:,.2f} AED")
                st.write(credits_df)

main()