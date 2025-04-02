import streamlit as st
import pandas as pd

# Load spreadsheet (can switch to Google Sheets URL later)
df = pd.read_excel("FM - West _ Project Tracker.xlsx", sheet_name="Project Tracker", skiprows=1)

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

st.markdown("---")
st.caption("Last updated manually from Excel. Live sync with Google Sheets available.")
