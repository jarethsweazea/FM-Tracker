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
    "AZ_Phoenix_720 W Highland Ave",
    "AZ_Tempe_1900 E 5th St",
    "AZ_Tucson_613 E Delano St",
    "CA_Anaheim_1560 S Lewis St",
    "CA_Costa Mesa_1750 Newport Blvd",
    "CA_Culver City_5668 Selmaraine Dr",
    "CA_Hayward_1025 A St",
    "CA_Huntington Beach_17531 Griffin Ln",
    "CA_Lawndale_16711 Hawthorne Blvd",
    "CA_Long Beach_1388 Daisy Ave",
    "CA_Los Angeles_5477 Alhambra Ave",
    "CA_Los Angeles_8600 W Pico Blvd",
    "CA_Los Angeles_417 S Hill St",
    "CA_Los Angeles_1411 W Sunset Blvd",
    "CA_Los Angeles_615 N Western Ave",
    "CA_Los Angeles_1842 W Washington Blvd",
    "CA_Los Angeles_5443 W Pico Blvd",
    "CA_Los Angeles_3000 S Bundy Dr",
    "CA_Los Angeles_3446 John St",
    "CA_Los Angeles_358 W 38th St",
    "CA_Los Angeles_2352 S Sepulveda Blvd",
    "CA_Mountain View_2150 Old Middlefield Way",
    "CA_Oakland_5333 Adeline St",
    "CA_Oakland_2353 E 12th St",
    "CA_Oceanside_3760 Oceanic Way",
    "CA_Pasadena_1060 E Colorado Blvd",
    "CA_Redwood City_426 MacArthur Ave",
    "CA_Sacramento_1501 N C St",
    "CA_San Diego_2707 Boston Ave",
    "CA_San Diego_6334 El Cajon Blvd",
    "CA_San Francisco_90 Charter Oak Ave",
    "CA_San Francisco_475 6th St",
    "CA_San Francisco_1200 Market St",
    "CA_San Jose_96 E Santa Clara St",
    "CA_San Jose_949 Ruff Dr",
    "CA_San Mateo_66 21st Ave",
    "CA_Santa Ana_2509 S Broadway",
    "CA_Sunnyvale_1026 W Evelyn Ave",
    "CA_Van Nuys_14435 Victory Blvd",
    "CO_Aurora_14200 E Alameda Ave",
    "CO_Denver_810 N Vallejo St",
    "CO_Denver_2171 S Grape St",
    "ID_Boise_1744 W Main St",
    "NV_Las Vegas_4215 S Durango Dr",
    "NV_Las Vegas_333 W St Louis Ave",
    "NV_Las Vegas_110 S Rainbow Blvd",
    "OR_Portland_1135 SE Grand Ave",
    "UT_Salt Lake City_23 N 900 W",
    "WA_Seattle_1525 13th Ave",
    "WA_Seattle_1601 Dexter Ave N",
    "WA_Seattle_5600 Roosevelt Way NE",
    "WA_Tacoma_3726 S G St"
]


# === Sidebar Filters ===
def parse_facility_parts(facility_string):
    parts = facility_string.split("_")
    return {
        "state": parts[0],
        "city": parts[1],
        "label": "_".join(parts[2:])  # This is the address part
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
# === Normalize the Facility column from the Sheet ===
def extract_parts(facility):
    try:
        parts = facility.split("_")
        state = parts[0]
        city = parts[1]
        address = "_".join(parts[2:])  # <- this fixes the issue
        return {"state": state, "city": city, "address": address}
    except:
        return {"state": "", "city": "", "address": ""}

facility_parts = df["Facility"].apply(extract_parts)
df["state"] = facility_parts.apply(lambda x: x["state"])
df["city"] = facility_parts.apply(lambda x: x["city"])
df["address"] = facility_parts.apply(lambda x: x["address"])
date_columns = ["Creation Date", "Initial Work Date", "Expected Completion Date", "Est. Start", "Actual Start", "Est. Completion", "Actual Completion"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%m/%d/%Y')



# === Apply filter selections ===
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

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = "https://api.servicechannel.com/v3/odata/workorders"
    params = {
    "$select": "Id,Number,LocationId,Caller,CreatedBy,CallDate,Priority,Trade,ApprovalCode",
    "$filter": "Status/Primary eq 'OPEN' or Status/Primary eq 'IN PROGRESS' or Status/Primary eq 'PENDING'",
    "$top": 1000
}


    all_results = []
    try:
        while url:
            response = requests.get(url, headers=headers, params=params)
            if not response.ok:
                return pd.DataFrame(), f"API error {response.status_code}: {response.text}"
            data = response.json()
            all_results.extend(data.get("value", []))
            url = data.get("@odata.nextLink")  # Follow next page
            params = None  # Only include params on first request
        return pd.json_normalize(all_results), None

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
        # === Parse and filter ticket data ===
        def extract_ticket_parts(location_name):
            try:
                parts = location_name.split("_")
                state = parts[0]
                city = parts[1]
                address = "_".join(parts[2:])
                return {"state": state, "city": city, "address": address}
            except:
                return {"state": "", "city": "", "address": ""}

        ticket_parts = ticket_df["LocationName"].apply(extract_ticket_parts)
        ticket_df["state"] = ticket_parts.apply(lambda x: x["state"])
        ticket_df["city"] = ticket_parts.apply(lambda x: x["city"])
        ticket_df["address"] = ticket_parts.apply(lambda x: x["address"])

        # === Apply sidebar filters ===
        if selected_facility != "All":
            ticket_df = ticket_df[ticket_df["address"].str.strip() == selected_facility.strip()]
        elif selected_city != "All":
            ticket_df = ticket_df[ticket_df["city"].str.strip() == selected_city.strip()]
        elif selected_state != "All":
            ticket_df = ticket_df[ticket_df["state"].str.strip() == selected_state.strip()]

        if ticket_df.empty:
            st.info("No maintenance tickets found for this selection.")
        else:
            st.dataframe(ticket_df)

st.markdown("---")
st.caption("Live synced with Google Sheets. Data updates automatically. Update requests are limited to once every 7 days per project.")
