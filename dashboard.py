import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from base64 import b64encode

# === Sheet URLs ===
sheet_url = "https://docs.google.com/spreadsheets/d/1FzLw6sHeLEed1e6ubijpjj2mNfG4B8UBJinO4KTe_ek/gviz/tq?tqx=out:csv&sheet=Project%20Tracker"
gsheet_edit_url = "https://docs.google.com/spreadsheets/d/1FzLw6sHeLEed1e6ubijpjj2mNfG4B8UBJinO4KTe_ek/edit#gid=0"
update_log_sheet_id = "1TAPw-tXHcYZRuZpSgcZs3TWs1AifGoAudEYVvB20lXs"

# === Load and prepare project data ===
df = pd.read_csv(sheet_url, skiprows=1)
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
df = df.dropna(subset=["Facility", "Project Name"])
date_columns = ["Creation Date", "Initial Work Date", "Expected Completion Date", "Est. Start", "Actual Start", "Est. Completion", "Actual Completion"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%m/%d/%Y')

# === Streamlit Setup ===
st.set_page_config(layout="wide")
st.title("📍 West Region Project Tracker")
tabs = st.tabs(["📋 Project Dashboard", "🚰 Maintenance Tickets"])

# === Color Tag Logic ===
status_colors = {
    "P0": "#FF4B4B",
    "P1": "#FFA500",
    "P2": "#1E90FF",
    "P3": "#9370DB",
    "Complete": "#28A745",
}

def get_status_color(status):
    return status_colors.get(status, "#CCCCCC")

# === Update Request Log ===
def fetch_recent_requests():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{update_log_sheet_id}/gviz/tq?tqx=out:csv&sheet=Log"
        log_df = pd.read_csv(url)
        log_df["Timestamp"] = pd.to_datetime(log_df["Timestamp"], errors='coerce')
        log_df["Project Name"] = log_df["Project Name"].astype(str).str.strip()
        log_df["Facility"] = log_df["Facility"].astype(str).str.strip()
        return log_df
    except:
        return pd.DataFrame(columns=["Project Name", "WO#", "Facility", "Status", "Timestamp"])

log_df = fetch_recent_requests()
log_df = log_df[log_df['Timestamp'] >= datetime.now() - timedelta(days=14)]

# === ServiceChannel Token ===
def get_servicechannel_token():
    url = "https://login.servicechannel.com/oauth/token"
    client_id = st.secrets["sc_client_id"]
    client_secret = st.secrets["sc_client_secret"]
    username = st.secrets["sc_username"]
    password = st.secrets["sc_password"]
    auth = b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
    payload = {"grant_type": "password", "username": username, "password": password}
    response = requests.post(url, data=payload, headers=headers)
    if response.ok:
        return response.json().get("access_token")
    else:
        return None

# === Fetch Open Tickets via /v3/workorders/search ===
def fetch_open_work_orders():
    token = get_servicechannel_token()
    if not token:
        return pd.DataFrame(), "Unable to retrieve access token."
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "statuses": ["Open"],
        "dateRange": {
            "startDate": "2024-01-01T00:00:00",
            "endDate": "2025-12-31T23:59:59"
        },
        "limit": 100
    }
    response = requests.post("https://api.servicechannel.com/v3/workorders/search", headers=headers, json=payload)
    if response.ok:
        data = response.json()
        if isinstance(data, dict) and "workOrders" in data:
            return pd.DataFrame(data["workOrders"]), None
        return pd.DataFrame(), "No work order data found."
    return pd.DataFrame(), f"API error: {response.status_code}"

# === Tab 1: Project Dashboard ===
with tabs[0]:
    facility_list = sorted(df["Facility"].unique())
    selected_facility = st.selectbox("Select Facility", ["All"] + facility_list)
    filtered_df = df if selected_facility == "All" else df[df["Facility"] == selected_facility]

    st.subheader(f"Projects at {selected_facility}" if selected_facility != "All" else "All Projects")
    for project in filtered_df["Project Name"].unique():
        project_data = filtered_df[filtered_df["Project Name"] == project].iloc[0]
        color = get_status_color(project_data["STATUS"])
        with st.expander(label=project, expanded=False):
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

            project_clean = str(project).strip()
            facility_clean = str(project_data["Facility"]).strip()
            recent = log_df[(log_df["Project Name"] == project_clean) & (log_df["Facility"] == facility_clean)]
            recent = recent[recent["Timestamp"] >= datetime.now() - timedelta(days=7)]

            if not recent.empty:
                last_ts = recent["Timestamp"].max()
                remaining = 7 - (datetime.now() - last_ts).days
                st.markdown(f"🛑 Update request unavailable. Last sent on {last_ts.strftime('%b %d, %Y')} — available again in {remaining} day(s).")
            else:
                if st.button(f"Request Update for {project}", key=f"button_{project}"):
                    webhook_url = "https://hooks.zapier.com/hooks/catch/18073884/2cco9aa/"
                    payload = {
                        "project_name": str(project),
                        "facility": str(project_data['Facility']),
                        "status": str(project_data['STATUS']),
                        "wo": str(project_data['WO#']),
                        "sheet_link": gsheet_edit_url,
                        "timestamp": datetime.now().isoformat()
                    }
                    try:
                        requests.post(webhook_url, json=payload, timeout=5)
                        st.success("Update request sent via Slack and logged successfully.")
                    except Exception as e:
                        st.error("Failed to send update request.")
                        st.text(str(e))

# === Tab 2: Maintenance Tickets ===
with tabs[1]:
    st.header("Open Maintenance Tickets")
    ticket_df, ticket_error = fetch_open_work_orders()
    if ticket_error:
        st.error(ticket_error)
    elif not ticket_df.empty:
        st.dataframe(ticket_df)
    else:
        st.info("No open work orders available — check if your account has access to regional or location-level data.")

st.markdown("---")
st.caption("Live synced with Google Sheets. Data updates automatically. Update requests are limited to once every 7 days per project.")
