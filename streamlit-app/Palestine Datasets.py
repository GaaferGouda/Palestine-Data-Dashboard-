import pandas as pd
import streamlit as st
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(page_title="Palestine Dashboard", layout="wide")

# --- Sidebar: Theme & File Uploads ---
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
text_color = "#FFFFFF" if theme == "Dark" else "#000000"

st.sidebar.subheader("📂 Upload Your Datasets")

uploaded_files = st.sidebar.file_uploader(
    "Upload any of the following CSVs:\n- Killed in Gaza\n- Press Killed in Gaza\n- Summary Data\n- Daily Casualties – Gaza\n- Daily Casualties – West Bank",
    type=["csv"],
    accept_multiple_files=True,
)

st.markdown(f"<h1 style='color:{text_color}'>Palestine Data Dashboard</h1>", unsafe_allow_html=True)

# --- Auto-detect column mapping ---
def detect_columns(df):
    col_map = {}
    col_map['date'] = next((c for c in df.columns if c.lower() in ['date','day','datetime','report_date']), None)
    col_map['killed'] = next((c for c in df.columns if c.lower() in ['killed','casualties','death','deaths','killed_cum']), None)
    col_map['children_killed'] = next((c for c in df.columns if 'child' in c.lower() and 'kill' in c.lower()), None)
    col_map['women_killed'] = next((c for c in df.columns if 'women' in c.lower() and 'kill' in c.lower()), None)
    col_map['injured'] = next((c for c in df.columns if 'injur' in c.lower()), None)
    col_map['aid_seeker_killed'] = next((c for c in df.columns if 'aid' in c.lower() and 'kill' in c.lower()), None)
    col_map['starved'] = next((c for c in df.columns if 'starv' in c.lower()), None)
    col_map['medical_killed'] = next((c for c in df.columns if 'medical' in c.lower() and 'kill' in c.lower()), None)
    col_map['journalists_killed'] = next((c for c in df.columns if 'journal' in c.lower() and 'kill' in c.lower()), None)
    col_map['first_responders_killed'] = next((c for c in df.columns if 'first' in c.lower() and 'respond' in c.lower() and 'kill' in c.lower()), None)
    col_map['settler_attacks'] = next((c for c in df.columns if 'settler' in c.lower() and 'attack' in c.lower()), None)
    col_map['infrastructure'] = next((c for c in df.columns if 'infra' in c.lower()), None)
    return col_map

# --- Load & merge any dataset ---
def load_and_prepare_csv(files):
    if not files:
        st.warning("No files uploaded yet.")
        return None

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        col_map = detect_columns(df)

        # Identify dataset type by filename
        filename = f.name.lower()
        if "gaza" in filename and "daily" in filename:
            region = "Gaza"
        elif "west" in filename:
            region = "West Bank"
        elif "press" in filename:
            region = "Press (Gaza)"
        elif "summary" in filename:
            region = "Summary"
        elif "infrastructure" in filename:
            region = "Infrastructure"
        else:
            region = "Other"

        # Ensure 'date' column
        if col_map['date'] and col_map['date'] in df.columns:
            df['date'] = pd.to_datetime(df[col_map['date']], errors='coerce')
        else:
            df['date'] = pd.date_range(start='2000-01-01', periods=len(df))
            st.warning(f"No date column in {f.name}. Using sequential dates.")

        # Fill missing key columns
        for key in ['killed','children_killed','women_killed','injured','aid_seeker_killed','starved',
                    'medical_killed','journalists_killed','first_responders_killed','settler_attacks','infrastructure']:
            df[key] = df[col_map[key]] if col_map[key] and col_map[key] in df.columns else 0

        df['region'] = region
        dfs.append(df)

    merged = pd.concat(dfs, ignore_index=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"merged_palestine_{timestamp}.csv"
    merged.to_csv(save_path, index=False, encoding='utf-8-sig')
    st.success(f"✅ All datasets merged successfully → {save_path}")
    return merged

# --- Load data
df_combined = load_and_prepare_csv(uploaded_files)

# --- Tabs ---
tab1, tab2 = st.tabs(["📊 Overview & Trends", "📥 Downloads"])

# --- Tab 1: Metrics + Chart ---
with tab1:
    if df_combined is not None:
        st.subheader("Key Figures")

        total_aid = df_combined['aid_seeker_killed'].sum()
        total_injured = df_combined['injured'].sum()
        total_children = df_combined['children_killed'].sum()
        total_starved = df_combined['starved'].sum()
        total_women = df_combined['women_killed'].sum()
        total_medical = df_combined['medical_killed'].sum()
        total_journalists = df_combined['journalists_killed'].sum()
        total_responders = df_combined['first_responders_killed'].sum()
        total_attacks = df_combined['settler_attacks'].sum()

        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)
        c7, c8 = st.columns(2)

        c1.metric("Attacked Seeking Aid", f"{total_aid:,}")
        c2.metric("Injured", f"{total_injured:,}")
        c3.metric("Children Killed", f"{total_children:,}")
        c4.metric("Starved to Death", f"{total_starved:,}")
        c5.metric("Women Killed", f"{total_women:,}")
        c6.metric("Medical Personnel Killed", f"{total_medical:,}")
        c7.metric("Journalists Killed", f"{total_journalists:,}")
        c8.metric("First Responders Killed", f"{total_responders:,}")
        st.markdown(f"**Settler Attacks:** {total_attacks:,}")

        st.markdown("---")

        # Filter by date
        df_combined = df_combined.sort_values('date')
        min_date, max_date = df_combined['date'].min(), df_combined['date'].max()
        start_date, end_date = st.slider(
            "Select Date Range",
            min_value=min_date.date(),
            max_value=max_date.date(),
            value=(min_date.date(), max_date.date())
        )

        mask = (df_combined['date'].dt.date >= start_date) & (df_combined['date'].dt.date <= end_date)
        df_filtered = df_combined[mask]

        # Daily casualties
        fig = px.line(
            df_filtered,
            x='date',
            y='killed',
            color='region',
            title=f"Daily Casualties ({start_date} → {end_date})",
            template="plotly_dark" if theme == "Dark" else "plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please upload at least one dataset file.")

# --- Tab 2: Downloads ---
with tab2:
    st.subheader("Download Merged Dataset")
    if df_combined is not None:
        csv = df_combined.to_csv(index=False).encode('utf-8-sig')
        json_data = df_combined.to_json(orient='records', force_ascii=False).encode('utf-8')
        st.download_button("⬇️ Download as CSV", csv, "palestine_data.csv", "text/csv")
        st.download_button("⬇️ Download as JSON", json_data, "palestine_data.json", "application/json")
