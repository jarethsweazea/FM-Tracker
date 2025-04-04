import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Load live Google Sheet as CSV
sheet_url = "https://docs.google.com/spreadsheets/d/1FzLw6sHeLEed1e6ubijpjj2mNfG4B8UBJinO4KTe_ek/gviz/tq?tqx=out:csv&sheet=Project%20Tracker"
gsheet_edit_url = "https://docs.google.com/spreadsheets/d/1FzLw6sHeLEed1e6ubijpjj2mNfG4B8UBJinO4KTe_ek/edit#gid=0"
update_log_sheet_id = "1zaFv1pci2U0UIAq-10CgY2MLoy2NCD9K1autIvGFplY"
df = pd.read_csv(sheet_url, skiprows=1)

# Rename key columns for clarity
df = df.rename(columns={
    df.columns[0]: "STATUS",
    df.columns[1]: "Phase",
    df.columns[2]: "Recent Status Update",
    df.columns[3]: "Region",
    df.columns[4]: "Facility",
    df.columns[5]: "Project Name",
    df.columns[6]: "WO#",
    df.columns[7]: "Creation Date",
    df.columns[8]: "Initial Work Date",
    df.columns[9]: "Expected Completion Date",
    df.columns[10]: "Project Summary",
    df.columns[20]: "Est. Cost",
    df.columns[21]: "Project Code",
    df.columns[22]: "Approved Cost",
    df.columns[23]: "Est. Start",
    df.columns[24]: "Actual Start",
    df.columns[25]: "Est. Completion",
    df.columns[26]: "Actual Completion",
    df.columns[27]: "Actual Cost",
    df.columns[28]: "Completion Status",
    df.columns[29]: "Completion Photos",
})

# Drop any rows that don't have a Facility or Project Name
df = df.dropna(subset=["Facility", "Project Name"])

# Format all date columns to remove time portion
date_columns = ["Creation Date", "Initial Work Date", "Expected Completion Date", "Est. Start", "Actual Start", "Est. Completion", "Actual Completion"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%m/%d/%Y')

st.set_page_config(page_title="West Region Project Dashboard", layout="wide")
st.title("📍 West Region Project Tracker")

# Sidebar filter as dropdown
facility_list = sorted(df["Facility"].unique())
selected_facility = st.sidebar.selectbox("Select Facility", ["All"] + facility_list)

if selected_facility != "All":
    filtered_df = df[df["Facility"] == selected_facility]
else:
    filtered_df = df

# Define status colors
status_colors = {
    "P0": "#FF4B4B",  # red
    "P1": "#FFA500",  # orange
    "P2": "#1E90FF",  # blue
    "P3": "#9370DB",  # purple
    "Complete": "#28A745",  # green
}

def get_status_color(status):
    return status_colors.get(status, "#CCCCCC")

# Initialize update log (read from CSV backup if needed)
def fetch_recent_requests():
    try:
        log_url = f"https://docs.google.com/spreadsheets/d/{update_log_sheet_id}/gviz/tq?tqx=out:csv&sheet=Log"
        log_df = pd.read_csv(log_url)
        log_df["Timestamp"] = pd.to_datetime(log_df["Timestamp"], errors='coerce')
        return log_df
    except:
        return pd.DataFrame(columns=["Project Name", "WO#", "Facility", "Status", "Timestamp"])

log_df = fetch_recent_requests()

# Main display: Table of Projects
st.subheader(f"Projects at {selected_facility}" if selected_facility != "All" else "All Projects")
project_names = filtered_df["Project Name"].unique()

for project in project_names:
    project_data = filtered_df[filtered_df["Project Name"] == project].iloc[0]
    color = get_status_color(project_data["STATUS"])
    with st.expander(label=f"{project}", expanded=False):
        status_tag = f"<span style='background-color:{color};color:white;padding:3px 8px;margin-right:10px;border-radius:4px;font-size:13px'>{project_data['STATUS']}</span>"
        st.markdown(f"{status_tag}", unsafe_allow_html=True)
        st.markdown(f"**Recent Update:** {project_data['Recent Status Update']}")
        st.markdown(f"**Project Summary:** {project_data['Project Summary']}")
        st.markdown(f"**Phase:** {project_data['Phase']}")
        st.markdown(f"**WO #:** {project_data['WO#']}")
        st.markdown(f"**Initial Work Date:** {project_data['Initial Work Date']}")
        st.markdown(f"**Expected Completion:** {project_data['Expected Completion Date']}")
        st.markdown(f"**Actual Completion:** {project_data['Actual Completion']}")
        st.markdown(f"**Est. Cost:** {project_data['Est. Cost']}")
        st.markdown(f"**Approved Cost:** {project_data['Approved Cost']}")
        st.markdown(f"**Project Code:** {project_data['Project Code']}")
        st.markdown(f"**Completion Status:** {project_data['Completion Status']}")

        # Check for existing request within the last 7 days
        recent_request = log_df[(log_df["Project Name"] == project) & (log_df["WO#"] == project_data["WO#"])]
        recent_request = recent_request[recent_request["Timestamp"] >= datetime.now() - timedelta(days=7)]

        if not recent_request.empty:
            last_ts = recent_request["Timestamp"].max()
            days_remaining = 7 - (datetime.now() - last_ts).days
            st.info(f"🕒 Update request already sent on {last_ts.strftime('%b %d, %Y')}. You can send another in {days_remaining} day(s).")
        else:
            if st.button(f"Request Update for {project}", key=f"button_{project}"):
                zapier_webhook_url = "https://hooks.zapier.com/hooks/catch/18073884/2cco9aa/"
                try:
                    payload = {
                        "project_name": str(project),
                        "facility": str(project_data['Facility']),
                        "status": str(project_data['STATUS']),
                        "wo": str(project_data['WO#']),
                        "sheet_link": gsheet_edit_url,
                        "timestamp": datetime.now().isoformat()
                    }
                    requests.post(zapier_webhook_url, json=payload, timeout=5)
                    st.success("Update request sent via Slack and logged successfully.")
                except Exception as e:
                    st.error("Failed to send update request.")
                    st.text(str(e))

st.markdown("---")
st.caption("Live synced with Google Sheets. Data updates automatically. Update requests are limited to once every 7 days per project.")
