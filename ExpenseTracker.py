import streamlit as st
import pandas as pd
import os
from datetime import datetime, time as dtime
import pytz
from fpdf import FPDF
from io import BytesIO

# -------- Page Config --------
st.set_page_config(page_title="📊 Business Expense Tracker", page_icon="📊", layout="wide")

# -------- Custom CSS Theme --------
st.markdown("""<style>
html, body, .stApp { background-color: #f5f1ed; font-family: 'Segoe UI', sans-serif; color: #071330; }
.stTextInput > div > label, .stNumberInput > div > label, .stDateInput > div > label,
.stTimeInput > div > label, .stTextArea > div > label {
    font-weight: 600; color: #d87d2f !important;
}
input, textarea, select {
    background-color: #ffffff !important; color: #071330 !important;
    border: 1px solid #d89c60 !important; border-radius: 8px !important;
    padding: 0.5rem !important;
}
.stTextArea textarea {
    resize: vertical; min-height: 100px; max-height: 300px;
}
.stButton>button {
    background: linear-gradient(135deg, #d89c60, #e87a00); color: white;
    font-weight: bold; border-radius: 8px; padding: 0.6rem 1.4rem; border: none;
    transition: background 0.3s ease;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #e87a00, #d89c60);
}
.stMarkdown h1, .stMarkdown h2 { color: #e87a00; }
.stCaption { color: #8a5a30; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
section[data-testid="time-input"] input {
    background-color: #ffffff !important; border: 1px solid #d89c60 !important;
    border-radius: 8px !important; padding: 0.5rem !important;
    color: #071330 !important; font-weight: 500;
}
section[data-testid="time-input"] > div {
    padding-left: 0px !important; padding-right: 0px !important;
}
[data-testid="stRadio"] > div {
    flex-direction: column;
    gap: 0.5rem;
}
[data-testid="stRadio"] label {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.6rem 1rem;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    background-color: #f3e4d7;
    transition: background 0.3s ease;
}
[data-testid="stRadio"] label:hover {
    background-color: #e2d3c1;
}
[data-testid="stRadio"] label[data-selected="true"] {
    background-color: #e87a00 !important;
    color: white !important;
}
</style>""", unsafe_allow_html=True)

# -------- Title --------
st.title("📊 Business Expense Tracker")
st.caption("Log, filter, analyze and export your expenses.")

# -------- Sidebar Navigation --------
with st.sidebar:
    st.markdown("### 📌 Choose Section")

    menu = st.radio(
        "Choose Section",
        ["💾 Add Expenses", "📂 View Expenses", "📈 Expense Summary"],
        index=["💾 Add Expenses", "📂 View Expenses", "📈 Expense Summary"].index(
            st.session_state.get("menu", "💾 Add Expenses")
        ),
        label_visibility="collapsed"
    )
    st.session_state["menu"] = menu

# -------- File Path --------
directory = os.getcwd()
file_name = "business_expenses.xlsx"
file_path = os.path.join(directory, file_name)

# -------- Add Expenses Tab --------
if menu == "💾 Add Expenses":
    st.header("💾 Expense Entry")

    col1, col2 = st.columns(2)

    with col1:
        amount = st.number_input("💰 Amount (INR)", min_value=0.0, step=1.0, format="%.0f")
        category = st.text_input("📂 Category", placeholder="e.g. Travel, Office")
        subcategory = st.text_input("🏷️ Subcategory", placeholder="e.g. Taxi, Food")

    with col2:
        description = st.text_area("📝 Description", placeholder="Detailed expense info", height=140)

    date_col, time_col = st.columns([1, 1])
    with date_col:
        date_input = st.date_input("📅 Date", value=datetime.now().date())
    with time_col:
        current_time = datetime.now().time()
        time_input = st.time_input("⏰ Time", value=dtime(current_time.hour, current_time.minute))

    ist = pytz.timezone("Asia/Kolkata")
    datetime_input = ist.localize(datetime.combine(date_input, time_input))

    if st.button("📏 Save Expense"):
        new_data = {
            "Amount (INR)": amount,
            "Category": category,
            "SubCategory": subcategory,
            "Description": description,
            "DateTime (IST)": datetime_input.strftime('%Y-%m-%d %H:%M:%S')
        }

        new_df = pd.DataFrame([new_data])
        try:
            if os.path.exists(file_path):
                existing_df = pd.read_excel(file_path)
                final_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                final_df = new_df

            final_df.to_excel(file_path, index=False)
            st.success(f"✅ Expense saved to `{file_path}`")
        except Exception as e:
            st.error(f"❌ Error saving file: {e}")

# -------- View Table Tab --------
elif menu == "📂 View Expenses":
    st.header("📂 View & Filter Expenses")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)

        with st.expander("🔎 Filter Options", expanded=False):
            cat_filter = st.multiselect("📁 Filter by Category", options=sorted(df["Category"].dropna().unique()))
            date_range = st.date_input("📆 Filter by Date Range", [])

        filtered_df = df.copy()
        if cat_filter:
            filtered_df = filtered_df[filtered_df["Category"].isin(cat_filter)]
        if len(date_range) == 2:
            start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            filtered_df["DateTime (IST)"] = pd.to_datetime(filtered_df["DateTime (IST)"])
            filtered_df = filtered_df[(filtered_df["DateTime (IST)"] >= start) & (filtered_df["DateTime (IST)"] <= end)]

        st.dataframe(filtered_df, use_container_width=True)

        # Display total filtered expense amount
        if not filtered_df.empty:
            total_amount = filtered_df["Amount (INR)"].sum()
            st.markdown(f"### 💸 Total Filtered Expenses: INR {total_amount:,.2f}")
        else:
            st.warning("⚠️ No matching expenses found for the selected filters.")

        # Edit/Delete Section
        st.markdown("---")
        st.subheader("✏️ Edit or 🗑️ Delete an Entry")

        if not filtered_df.empty:
            row_to_edit = st.selectbox("Select a row to edit/delete", filtered_df.index.tolist())
            selected_row = filtered_df.loc[row_to_edit]

            with st.form("edit_form"):
                new_amount = st.number_input("💰 Amount", value=selected_row["Amount (INR)"], format="%.2f")
                new_category = st.text_input("📂 Category", value=selected_row["Category"])
                new_subcat = st.text_input("🏷️ Subcategory", value=selected_row["SubCategory"])
                new_desc = st.text_area("📝 Description", value=selected_row["Description"])
                new_date = st.date_input("📅 Date", value=pd.to_datetime(selected_row["DateTime (IST)"]).date())
                new_time = st.time_input("⏰ Time", value=pd.to_datetime(selected_row["DateTime (IST)"]).time())

                submit_edit = st.form_submit_button("📏 Update Entry")
                delete_entry = st.form_submit_button("🗑️ Delete Entry")

            full_df = pd.read_excel(file_path)
            full_df["DateTime (IST)"] = pd.to_datetime(full_df["DateTime (IST)"])

            if submit_edit:
                full_df.loc[row_to_edit] = {
                    "Amount (INR)": new_amount,
                    "Category": new_category,
                    "SubCategory": new_subcat,
                    "Description": new_desc,
                    "DateTime (IST)": datetime.combine(new_date, new_time).strftime('%Y-%m-%d %H:%M:%S')
                }
                full_df.to_excel(file_path, index=False)
                st.success("✅ Entry updated successfully!")
                st.rerun()

            if delete_entry:
                full_df = full_df.drop(index=row_to_edit)
                full_df.to_excel(file_path, index=False)
                st.success("🗑️ Entry deleted successfully!")
                st.rerun()

        def create_pdf(data):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.set_fill_color(216, 156, 96)
            pdf.set_text_color(0)

            pdf.cell(0, 10, txt="Expense Report", ln=True, align='C')
            pdf.ln(5)

            headers = ["DateTime", "Amount", "Category", "SubCategory", "Description"]
            col_widths = [40, 25, 30, 30, 65]

            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 10, h, 1, 0, 'C')
            pdf.ln()

            for _, row in data.iterrows():
                values = [
                    str(row['DateTime (IST)']),
                    f"INR {row['Amount (INR)']}",
                    str(row['Category']),
                    str(row['SubCategory']),
                    str(row['Description'])
                ]
                for i, val in enumerate(values):
                    pdf.cell(col_widths[i], 10, val, 1)
                pdf.ln()

            return pdf

        pdf = create_pdf(filtered_df)
        pdf_bytes = BytesIO()
        pdf_bytes.write(pdf.output(dest="S").encode("latin1"))
        pdf_bytes.seek(0)

        st.subheader("📄 Export Filtered Data")
        colA, colB = st.columns(2)
        with colA:
            st.download_button("📅 Download Filtered PDF", data=pdf_bytes, file_name="filtered_expense_report.pdf", mime="application/pdf")
        with colB:
            if st.button("📏 Save Filtered PDF to Directory"):
                pdf_file_path = file_path.replace(".xlsx", "_filtered_report.pdf")
                pdf = create_pdf(filtered_df)
                pdf.output(pdf_file_path)
                st.success(f"✅ PDF saved to `{pdf_file_path}`")

    else:
        st.info("ℹ️ No data file found. Please save at least one entry to enable viewing.")

# -------- Charts Tab --------
elif menu == "📈 Expense Summary":
    st.header("📈 Expense Summary")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df["DateTime (IST)"] = pd.to_datetime(df["DateTime (IST)"])
        df["Date"] = df["DateTime (IST)"].dt.date

        with st.expander("📊 Charts"):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 By Category")
                cat_totals = df.groupby("Category")["Amount (INR)"].sum().sort_values(ascending=False)
                st.bar_chart(cat_totals)

            with col2:
                st.subheader("📈 By Date")
                date_totals = df.groupby("Date")["Amount (INR)"].sum()
                st.line_chart(date_totals)
    else:
        st.info("ℹ️ No data file found. Please save at least one entry to view charts.")
