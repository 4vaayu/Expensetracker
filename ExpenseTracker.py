import streamlit as st
import pandas as pd
import os
from datetime import datetime, time as dtime
import pytz
from fpdf import FPDF

# -------- Page Config --------
st.set_page_config(page_title="📊 Business Expense Tracker", page_icon="📊", layout="centered")

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
</style>""", unsafe_allow_html=True)

# -------- Title --------
st.title("📊 Business Expense Tracker")
st.caption("Log, filter, analyze and export your expenses.")

# -------- Input Section --------
st.header("🧾 Expense Entry")

col1, col2 = st.columns(2)

with col1:
    amount = st.number_input("💰 Amount (INR)", min_value=0.0, step=1.0, format="%.0f")
    category = st.text_input("📂 Category", placeholder="e.g. Travel, Office")
    subcategory = st.text_input("🏷️ Subcategory", placeholder="e.g. Taxi, Food")

with col2:
    description = st.text_area("📝 Description", placeholder="Detailed expense info", height=140)

date_col, time_col = st.columns([1, 1])
with date_col:
    date_input = st.date_input("Date", value=datetime.now().date())
with time_col:
    current_time = datetime.now().time()
    time_input = st.time_input("Time", value=dtime(current_time.hour, current_time.minute))

# IST Time
ist = pytz.timezone("Asia/Kolkata")
datetime_input = ist.localize(datetime.combine(date_input, time_input))

# -------- File Handling --------
st.header("💾 Save to Excel")
directory = st.text_input("📁 Directory Path", value=os.getcwd())
file_name = st.text_input("📄 Excel File Name (.xlsx)", value="business_expenses.xlsx")
file_path = os.path.join(directory, file_name)

if st.button("💾 Save Expense"):
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

# -------- Data Viewer --------
if os.path.exists(file_path):
    st.header("📂 View & Filter Expenses")

    df = pd.read_excel(file_path)

    # Filters
    with st.expander("🔎 Filter Options", expanded=False):
        cat_filter = st.multiselect("Filter by Category", options=sorted(df["Category"].dropna().unique()))
        date_range = st.date_input("Filter by Date Range", [], help="Select start and end dates")

        filtered_df = df.copy()
        if cat_filter:
            filtered_df = filtered_df[filtered_df["Category"].isin(cat_filter)]
        if len(date_range) == 2:
            start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            filtered_df["DateTime (IST)"] = pd.to_datetime(filtered_df["DateTime (IST)"])
            filtered_df = filtered_df[(filtered_df["DateTime (IST)"] >= start) & (filtered_df["DateTime (IST)"] <= end)]

    st.dataframe(filtered_df, use_container_width=True)

    # -------- Summary Charts --------
    st.header("📈 Expense Summary")

    with st.expander("📊 Charts"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("By Category")
            cat_totals = filtered_df.groupby("Category")["Amount (INR)"].sum().sort_values(ascending=False)
            st.bar_chart(cat_totals)

        with col2:
            st.subheader("By Date")
            filtered_df["Date"] = pd.to_datetime(filtered_df["DateTime (IST)"]).dt.date
            date_totals = filtered_df.groupby("Date")["Amount (INR)"].sum()
            st.line_chart(date_totals)

    # -------- Export to PDF --------
    st.header("📤 Export Options")

    def export_pdf(data: pd.DataFrame, pdf_path: str):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.set_fill_color(216, 156, 96)
        pdf.cell(0, 10, "Expense Report", ln=True, align='C')

        # Table headers
        pdf.set_font("Arial", 'B', 9)
        headers = ["DateTime", "Amount", "Category", "SubCategory", "Description"]
        col_widths = [35, 20, 30, 30, 75]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, border=1, align='C')
        pdf.ln()

        # Table rows
        pdf.set_font("Arial", size=9)
        for _, row in data.iterrows():
            pdf.cell(col_widths[0], 8, str(row["DateTime (IST)"]), border=1)
            pdf.cell(col_widths[1], 8, f"INR {int(row['Amount (INR)'])}", border=1)
            pdf.cell(col_widths[2], 8, str(row["Category"]), border=1)
            pdf.cell(col_widths[3], 8, str(row["SubCategory"]), border=1)
            pdf.cell(col_widths[4], 8, str(row["Description"]), border=1)
            pdf.ln()

        pdf.output(pdf_path)

    if st.button("📄 Export to PDF"):
        pdf_file = file_path.replace(".xlsx", "_report.pdf")
        export_pdf(filtered_df, pdf_file)
        st.success(f"✅ PDF exported to `{pdf_file}`")

else:
    st.info("ℹ️ No data file found. Please save at least one entry to enable viewing and exporting.")
