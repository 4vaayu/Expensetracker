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
        ["💾 Add Expenses", "📂 View Expenses", "📈 Expense Summary", "👥 Splitwise Console"],
        label_visibility="collapsed"
    )

# -------- File Path --------
directory = os.getcwd()
file_name = "business_expenses.xlsx"
file_path = os.path.join(directory, file_name)

members = ["Satish Yadav", "Sathish Kumar", "Arun Kumar", "Deepak GL", "Aman Singh"]

# -------- Add Expenses --------
if menu == "💾 Add Expenses":
    st.header("💾 Expense Entry")
    col1, col2 = st.columns(2)

    with col1:
        amount = st.number_input("💰 Amount (INR)", min_value=0.0, step=1.0, format="%.0f")
        category = st.text_input("📂 Category", placeholder="e.g. Travel, Office")
        subcategory = st.text_input("🏷️ Subcategory", placeholder="e.g. Taxi, Food")
        paid_by = st.selectbox("👤 Paid By", members)

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
            "PaidBy": paid_by,
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

# -------- View Expenses --------
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

        if not filtered_df.empty:
            total_amount = filtered_df["Amount (INR)"].sum()
            st.markdown(f"### 💸 Total Filtered Expenses: INR {total_amount:,.2f}")
        else:
            st.warning("⚠️ No matching expenses found.")

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
                new_paid_by = st.selectbox("👤 Paid By", members, index=members.index(selected_row["PaidBy"]) if selected_row["PaidBy"] in members else 0)
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
                    "PaidBy": new_paid_by,
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

            headers = ["DateTime", "Amount", "Category", "SubCategory", "Description", "PaidBy"]
            col_widths = [35, 20, 25, 25, 55, 25]
            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 10, h, 1, 0, 'C')
            pdf.ln()

            for _, row in data.iterrows():
                values = [
                    str(row['DateTime (IST)']),
                    f"{row['Amount (INR)']}",
                    str(row['Category']),
                    str(row['SubCategory']),
                    str(row['Description']),
                    str(row['PaidBy'])
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
                pdf.output(pdf_file_path)
                st.success(f"✅ PDF saved to `{pdf_file_path}`")

    else:
        st.info("ℹ️ No data file found. Please add at least one entry.")

# -------- Charts --------
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
        st.info("ℹ️ No data file found.")
elif menu == "👥 Splitwise Console":
    st.header("👥 Splitwise Console")

    paid_file = file_path.replace(".xlsx", "_paid_records.xlsx")
    advance_file = file_path.replace(".xlsx", "_advance_records.xlsx")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)

        if "PaidBy" not in df.columns:
            st.warning("⚠️ 'PaidBy' column not found. Please ensure new expenses include 'PaidBy' info.")
        else:
            df = df[df["PaidBy"].isin(members)]
            df["Amount (INR)"] = pd.to_numeric(df["Amount (INR)"], errors='coerce')
            df = df.dropna(subset=["Amount (INR)", "PaidBy"])

            paid_df = pd.read_excel(paid_file) if os.path.exists(paid_file) else pd.DataFrame(columns=["Payer", "Payee", "Owes", "Description", "DateTime"])
            advance_df = pd.read_excel(advance_file) if os.path.exists(advance_file) else pd.DataFrame(columns=["From", "To", "Amount", "DateTime"])

            split_records = []
            total_paid = {member: 0.0 for member in members}
            advance_paid = {member: 0.0 for member in members}

            for _, row in df.iterrows():
                payer = row["PaidBy"]
                amount = row["Amount (INR)"]
                desc = row.get("Description", "")
                dt = row.get("DateTime (IST)", "")
                per_head = round(amount / len(members), 2)

                total_paid[payer] += amount

                for member in members:
                    if member != payer:
                        entry = {
                            "Payer": payer,
                            "Payee": member,
                            "Owes": per_head,
                            "Description": desc,
                            "DateTime": dt
                        }
                        if not ((paid_df["Payer"] == payer) & (paid_df["Payee"] == member) & (paid_df["DateTime"] == dt)).any():
                            split_records.append(entry)

            if split_records:
                split_df = pd.DataFrame(split_records)

                # Advance Payment Input
                st.subheader("💰 Record Advance Payment")
                col1, col2, col3 = st.columns(3)
                with col1:
                    adv_from = st.selectbox("Paid By", members, key="adv_from")
                with col2:
                    adv_to = st.selectbox("Paid To", [m for m in members if m != adv_from], key="adv_to")
                with col3:
                    adv_amount = st.number_input("Amount (INR)", min_value=0.0, format="%.2f", key="adv_amount")

                adv_date = st.date_input("Date of Payment", key="adv_date")

                if st.button("➕ Add Advance Payment"):
                    new_adv = pd.DataFrame([{
                        "From": adv_from,
                        "To": adv_to,
                        "Amount": adv_amount,
                        "DateTime": str(adv_date)
                    }])
                    advance_df = pd.concat([advance_df, new_adv], ignore_index=True)
                    advance_df.to_excel(advance_file, index=False)
                    st.success(f"✅ Recorded ₹{adv_amount:.2f} advance from {adv_from} to {adv_to}")
                    st.rerun()

                # 👤 Select User to Settle Dues
                st.subheader("👤 Select User to Settle Dues")
                selected_payee = st.selectbox("Select a user to view or mark dues as paid", options=members)

                if selected_payee:
                    user_dues = split_df[split_df["Payee"] == selected_payee]
                    with st.expander(f"🔍 Outstanding dues for {selected_payee}", expanded=True):
                        if user_dues.empty:
                            # Show what others owe to this user
                            others_owe = split_df[split_df["Payer"] == selected_payee]
                            total_owed_to_user = others_owe["Owes"].sum()

                            if total_owed_to_user > 0:
                                st.info(f"✅ {selected_payee} has no dues to pay.\n\n💰 Others owe **₹{total_owed_to_user:.2f}** to them.")
                                for _, row in others_owe.iterrows():
                                    st.markdown(f"➡️ `{row['Payee']}` owes **₹{row['Owes']:.2f}** to `{selected_payee}` for _{row['Description']}_ on `{row['DateTime']}`")
                            else:
                                st.success(f"✅ {selected_payee} has no dues and no one owes them anything.")
                        else:
                            total_due = user_dues["Owes"].sum()
                            st.warning(f"🧾 {selected_payee} owes a total of **₹{total_due:.2f}** to others.")
                            for _, row in user_dues.iterrows():
                                st.markdown(f"➡️ `{selected_payee}` owes **₹{row['Owes']:.2f}** to `{row['Payer']}` for _{row['Description']}_ on `{row['DateTime']}`")

                            if st.checkbox(f"✅ Confirm you want to settle all dues for {selected_payee}"):
                                if st.button(f"💸 Mark All as Paid for {selected_payee}"):
                                    paid_df = pd.concat([paid_df, user_dues], ignore_index=True)
                                    paid_df.to_excel(paid_file, index=False)
                                    st.success(f"✅ All dues settled for {selected_payee}!")
                                    st.rerun()

                # 📉 Net Balances
                st.markdown("---")
                net_balances = {member: 0.0 for member in members}
                for row in split_df.to_dict(orient="records"):
                    net_balances[row["Payee"]] -= row["Owes"]
                    net_balances[row["Payer"]] += row["Owes"]

                if not advance_df.empty:
                    for _, row in advance_df.iterrows():
                        payer = row["From"]
                        receiver = row["To"]
                        amount = row["Amount"]
                        net_balances[payer] += amount
                        net_balances[receiver] -= amount
                        advance_paid[payer] += amount

                total_expense = sum(total_paid.values())
                share_per_person = round(total_expense / len(members), 2)

                st.subheader("📉 Net Balances")
                settlement_data = []

                for member in members:
                    pending = round(total_paid[member] + advance_paid[member] - share_per_person, 2)
                    owes_to = None
                    if pending < 0:
                        potential_creditors = {m: net_balances[m] for m in members if net_balances[m] > 0}
                        if potential_creditors:
                            owes_to = max(potential_creditors, key=potential_creditors.get)
                    settlement_data.append({
                        "Member": member,
                        "Total Paid (INR)": round(total_paid[member], 2),
                        "Advance Paid (INR)": round(advance_paid[member], 2),
                        "Share Owed (INR)": share_per_person,
                        "Pending (INR)": pending,
                        "Owes To": owes_to if owes_to else "—"
                    })

                settlement_df = pd.DataFrame(settlement_data)
                st.dataframe(settlement_df, use_container_width=True)
                st.markdown(f"💰 **Total Group Expense:** ₹{total_expense:.2f}")

                # 📬 Settlement Suggestions
                st.subheader("📬 Settlement Suggestions")
                pending_balances = {row["Member"]: row["Pending (INR)"] for row in settlement_data}
                creditors = {m: amt for m, amt in pending_balances.items() if amt > 0}
                debtors = {m: -amt for m, amt in pending_balances.items() if amt < 0}

                settlements = []
                for debtor, debt_amt in debtors.items():
                    for creditor, cred_amt in list(creditors.items()):
                        if debt_amt == 0:
                            break
                        pay_amt = min(debt_amt, cred_amt)
                        settlements.append(f"💸 `{debtor}` should pay **₹{pay_amt:.2f}** to `{creditor}`")
                        debt_amt -= pay_amt
                        creditors[creditor] -= pay_amt
                        if creditors[creditor] == 0:
                            del creditors[creditor]
                        if debt_amt == 0:
                            break

                if settlements:
                    for s in settlements:
                        st.markdown(s)
                else:
                    st.success("✅ All expenses are settled!")

            else:
                st.success("✅ All expenses are settled!")
    else:
        st.warning("⚠️ Expense file not found. Please add expenses first.")
