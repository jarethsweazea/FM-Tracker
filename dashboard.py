import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from base64 import b64encode

# === Streamlit Setup ===
st.set_page_config(layout="wide")
st.title("📍 West Region Project Tracker")
tabs = st.tabs(["📋 Project Dashboard", "🛠 Maintenance Tickets"])

# === Sheet URLs ===
sheet_url = "https://docs.google.com/spreadsheets/d/1FzLw6sHeLEed1e6ubijpjj2mNfG4B8UBJinO4KTe_ek/gviz/tq?tqx=out:csv&sheet=Project%20Tracker"
gsheet_edit_url = "https://docs.google.com/spreadsheets/d/1FzLw6sHeLEed1e6ubijpjj2mNfG4B8UBJinO4KTe_ek/edit#gid=0"
update_log_sheet_id = "1TAPw-tXHcYZRuZpSgcZs3TWs1AifGoAudEYVvB20lXs"

# === Full West Region Facility List ===
full_facility_list = [
    "USA - AZ - Phoenix - Midtown - 720 W Highland Ave",
    "USA - AZ - Tempe - ASU - 1900 E 5th St",
    "USA - AZ - Tucson - U of A - 613 E Delano St",
    "USA - CA - Anaheim - Anaheim Resort - 1560 S Lewis St",
    "USA - CA - Costa Mesa - Triangle Square - 1750 Newport Blvd",
    "USA - CA - Culver City - Fox Hills - 5668 Selmaraine Dr",
    "USA - CA - Hayward - Hayward - 1025 A St",
    "USA - CA - Huntington Beach - Downtown - 17531 Griffin Ln",
    "USA - CA - Lawndale - South Bay - 16711 Hawthorne Blvd",
    "USA - CA - Long Beach - Downtown - 1388 Daisy Ave",
    "USA - CA - Los Angeles - Alhambra - 5477 Alhambra Ave",
    "USA - CA - Los Angeles - Beverly Hills - 8600 W Pico Blvd",
    "USA - CA - Los Angeles - Downtown - 417 S Hill St",
    "USA - CA - Los Angeles - Echo Park - 1411 W Sunset Blvd",
    "USA - CA - Los Angeles - Hollywood - 615 N Western Ave",
    "USA - CA - Los Angeles - Koreatown - 1842 W Washington Blvd",
    "USA - CA - Los Angeles - Mid-City - 5443 W Pico Blvd",
    "USA - CA - Los Angeles - Santa Monica - 3000 S Bundy Dr",
    "USA - CA - Los Angeles - Silverlake - 3446 John St",
    "USA - CA - Los Angeles - University Park - 358 W 38th St",
    "USA - CA - Los Angeles - West LA - 2352 S Sepulveda Blvd",
    "USA - CA - Mountain View - Downtown - 2150 Old Middlefield Way",
    "USA - CA - Oakland - Berkeley - 5333 Adeline St",
    "USA - CA - Oakland - Downtown - 2353 E 12th St",
    "USA - CA - Oceanside - North County - 3760 Oceanic Way",
    "USA - CA - Pasadena - Old Town - 1060 E Colorado Blvd",
    "USA - CA - Redwood City - Downtown - 426 MacArthur Ave",
    "USA - CA - Sacramento - Downtown - 1501 N C St",
    "USA - CA - San Diego - Downtown - 2707 Boston Ave",
    "USA - CA - San Diego - SDSU - 6334 El Cajon Blvd",
    "USA - CA - San Francisco - Lower Mission - 90 Charter Oak Ave",
    "USA - CA - San Francisco - SoMa - 475 6th St",
    "USA - CA - San Francisco - Union Square - 1200 Market St",
    "USA - CA - San Jose - Downtown - 96 E Santa Clara St",
    "USA - CA - San Jose - North - 949 Ruff Dr",
    "USA - CA - San Mateo - Downtown - 66 21st Ave",
    "USA - CA - Santa Ana - South Coast Metro - 2509 S Broadway",
    "USA - CA - Sunnyvale - Downtown - 1026 W Evelyn Ave",
    "USA - CA - Van Nuys - San Fernando Valley - 14435 Victory Blvd",
    "USA - CO - Aurora - Town Center Mall - 14200 E Alameda Ave",
    "USA - CO - Denver - Downtown - 810 N Vallejo St",
    "USA - CO - Denver - South - 2171 S Grape St",
    "USA - ID - Boise - West End - 1744 W Main St",
    "USA - NV - Las Vegas - Durango - 4215 S Durango Dr",
    "USA - NV - Las Vegas - North Strip - 333 W St Louis Ave",
    "USA - NV - Las Vegas - Summerlin - 110 S Rainbow Blvd",
    "USA - OR - Portland - Inner Southeast - 1135 SE Grand Ave",
    "USA - UT - Salt Lake City - Downtown - 23 N 900 W",
    "USA - WA - Seattle - Capitol Hill - 1525 13th Ave",
    "USA - WA - Seattle - South Lake Union - 1601 Dexter Ave N",
    "USA - WA - Seattle - U-District - 5600 Roosevelt Way NE",
    "USA - WA - Tacoma - Lincoln District - 3726 S G St"
]

# === Sidebar Filters (simplified to State, City, Facility with Reset Button) ===
def parse_facility_parts(facility_string):
    parts = facility_string.split(" - ")
    return {
        "state": parts[1],
        "city": parts[2],
        "label": parts[-1]  # Address
    }


parsed_facilities = [parse_facility_parts(f) for f in full_facility_list]

with st.sidebar:
    if st.button("Clear Filters"):
        st.session_state["selected_state"] = "All"
        st.session_state["selected_city"] = "All"
        st.session_state["selected_facility"] = "All"

    state_options = sorted(set(f["state"] for f in parsed_facilities))
    selected_state = st.selectbox("Select State", ["All"] + state_options, key="selected_state")

    city_options = sorted(set(f["city"] for f in parsed_facilities if selected_state == "All" or f["state"] == selected_state))
    selected_city = st.selectbox("Select City", ["All"] + city_options, key="selected_city")

    filtered_facilities = [
        f["label"] for f in parsed_facilities
        if (selected_state in ["All", f["state"]]) and
           (selected_city in ["All", f["city"]])
    ]

    selected_facility = st.selectbox("Select Facility", ["All"] + filtered_facilities, key="selected_facility")


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

def extract_parts(facility):
    try:
        parts = facility.split("_")
        return {
            "state": parts[0],
            "city": parts[1],
            "address": "_".join(parts[2:])  # Handles multi-word streets
        }
    except:
        return {"state": "", "city": "", "address": ""}

facility_parts = df["Facility"].apply(extract_parts)
df["state"] = facility_parts.apply(lambda x: x["state"])
df["city"] = facility_parts.apply(lambda x: x["city"])
df["address"] = facility_parts.apply(lambda x: x["address"])

if selected_facility != "All":
    df = df[df["address"].str.strip() == selected_facility.strip()]
elif selected_city != "All":
    df = df[df["city"].str.strip() == selected_city.strip()]
elif selected_state != "All":
    df = df[df["state"].str.strip() == selected_state.strip()]




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

# === Fetch All Work Orders ===
def fetch_all_open_work_orders():
    token = get_servicechannel_token()
    if not token:
        return pd.DataFrame(), "Unable to retrieve access token."

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    url = "https://api.servicechannel.com/v3/odata/workorders"
    params = {
        "$select": "Id,Number,PurchaseOrderNumber,LocationId,Caller,CreatedBy,CallDate,Priority,Trade,ApprovalCode",
        "$filter": "Status/Primary eq 'OPEN'",
        "$top": 1000
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if not response.ok:
            return pd.DataFrame(), f"API error {response.status_code}: {response.text}"
        data = response.json()
        return pd.json_normalize(data.get("value", [])), None
    except Exception as e:
        return pd.DataFrame(), f"Exception fetching work orders: {str(e)}"

# === Project Dashboard ===
with tabs[0]:
    st.subheader("Projects")
    filtered_df = df

    if filtered_df.empty:
        st.warning("No projects in progress for this selection.")
    else:
        for project in filtered_df["Project Name"].unique():
            project_data = filtered_df[filtered_df["Project Name"] == project].iloc[0]
            color = get_status_color(project_data["STATUS"])
            with st.expander(f"{project}", expanded=False):
                status_tag = f"<span style='background-color:{color};color:white;padding:3px 8px;margin-right:10px;border-radius:4px;font-size:13px'>{project_data['STATUS']}</span>"
                st.markdown(status_tag, unsafe_allow_html=True)
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

                project_name_clean = str(project).strip()
                facility_clean = str(project_data["Facility"]).strip()
                recent_request = log_df[(log_df["Project Name"] == project_name_clean) & (log_df["Facility"] == facility_clean)]
                recent_request = recent_request[recent_request["Timestamp"] >= datetime.now() - timedelta(days=7)]

                if not recent_request.empty:
                    last_ts = recent_request["Timestamp"].max()
                    days_remaining = 7 - (datetime.now() - last_ts).days
                    st.markdown(f"🛑 Update request unavailable. Last sent on {last_ts.strftime('%b %d, %Y')} — available again in {days_remaining} day(s).")
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

# === Tab 2: Maintenance Tickets ===
with tabs[1]:
    st.subheader("Open Maintenance Tickets")
    ticket_df, ticket_error = fetch_all_open_work_orders()
    if ticket_error:
        st.error(ticket_error)
    elif ticket_df.empty:
        st.info("No work order data available.")
    else:
        st.dataframe(ticket_df)

st.markdown("---")
st.caption("Live synced with Google Sheets. Data updates automatically. Update requests are limited to once every 7 days per project.")
