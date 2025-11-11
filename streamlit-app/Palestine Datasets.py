import pandas as pd
import streamlit as st
import plotly.express as px
import os

st.set_page_config(page_title="Palestine Dashboard", layout="wide")

# --- Sidebar: Theme & File Uploads ---
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
text_color = "#FFFFFF" if theme=="Dark" else "#000000"

st.sidebar.subheader("Upload your datasets")
uploaded_gaza_list = st.sidebar.file_uploader(
    "Daily Gaza CSVs", type=["csv"], accept_multiple_files=True
)
uploaded_westbank_list = st.sidebar.file_uploader(
    "Daily West Bank CSVs", type=["csv"], accept_multiple_files=True
)

st.markdown(f"<h1 style='color:{text_color}'>Palestine Data Dashboard</h1>", unsafe_allow_html=True)

# --- Auto-detect column mapping ---
def detect_columns(df):
    col_map = {}
    col_map['date'] = next((c for c in df.columns if c.lower() in ['date','day','datetime','report_date']), None)
    col_map['killed'] = next((c for c in df.columns if c.lower() in ['killed','casualties','death','killed_cum']), None)
    col_map['children_killed'] = next((c for c in df.columns if 'children' in c.lower() and 'killed' in c.lower()), None)
    col_map['women_killed'] = next((c for c in df.columns if 'women' in c.lower() and 'killed' in c.lower()), None)
    col_map['injured'] = next((c for c in df.columns if 'injured' in c.lower()), None)
    col_map['aid_seeker_killed'] = next((c for c in df.columns if 'aid' in c.lower() and 'killed' in c.lower()), None)
    col_map['starved'] = next((c for c in df.columns if 'starve' in c.lower()), None)
    col_map['medical_killed'] = next((c for c in df.columns if 'medical' in c.lower() and 'killed' in c.lower()), None)
    col_map['journalists_killed'] = next((c for c in df.columns if 'journalist' in c.lower() and 'killed' in c.lower()), None)
    col_map['first_responders_killed'] = next((c for c in df.columns if 'first responder' in c.lower() and 'killed' in c.lower()), None)
    col_map['settler_attacks'] = next((c for c in df.columns if 'settler' in c.lower() and 'attack' in c.lower()), None)
    return col_map

# --- Load, merge, and save CSVs ---
def load_and_merge_csv(files, region_name=None):
    if not files:
        return None
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        col_map = detect_columns(df)
        
        # Ensure 'date' column
        if col_map['date'] and col_map['date'] in df.columns:
            df['date'] = pd.to_datetime(df[col_map['date']])
        else:
            st.warning(f"No date column detected in file {f.name}. Using default sequential index as date.")
            df['date'] = pd.date_range(start='2000-01-01', periods=len(df))
        
        # Ensure 'killed' column
        df['killed'] = df[col_map['killed']] if col_map['killed'] and col_map['killed'] in df.columns else 0
        df['children_killed'] = df[col_map['children_killed']] if col_map['children_killed'] and col_map['children_killed'] in df.columns else 0
        df['women_killed'] = df[col_map['women_killed']] if col_map['women_killed'] and col_map['women_killed'] in df.columns else 0
        df['injured'] = df[col_map['injured']] if col_map['injured'] and col_map['injured'] in df.columns else 0
        df['aid_seeker_killed'] = df[col_map['aid_seeker_killed']] if col_map['aid_seeker_killed'] and col_map['aid_seeker_killed'] in df.columns else 0
        df['starved'] = df[col_map['starved']] if col_map['starved'] and col_map['starved'] in df.columns else 0
        df['medical_killed'] = df[col_map['medical_killed']] if col_map['medical_killed'] and col_map['medical_killed'] in df.columns else 0
        df['journalists_killed'] = df[col_map['journalists_killed']] if col_map['journalists_killed'] and col_map['journalists_killed'] in df.columns else 0
        df['first_responders_killed'] = df[col_map['first_responders_killed']] if col_map['first_responders_killed'] and col_map['first_responders_killed'] in df.columns else 0
        df['settler_attacks'] = df[col_map['settler_attacks']] if col_map['settler_attacks'] and col_map['settler_attacks'] in df.columns else 0

        df['region'] = region_name if region_name else 'Unknown'
        dfs.append(df)
    
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Save merged CSV locally
    save_path = f"merged_{region_name.lower().replace(' ','_')}.csv"
    merged_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    st.success(f"Merged {region_name} data saved to {save_path}")
    
    return merged_df

# --- Load Data ---
df_gaza_daily = load_and_merge_csv(uploaded_gaza_list, "Gaza")
df_westbank_daily = load_and_merge_csv(uploaded_westbank_list, "West Bank")

# --- Tabs ---
tab1, tab2 = st.tabs(["📈 Daily Casualties & Key Figures", "📥 Download Datasets"])

# --- Tab 1: Key Figures + Daily Casualties Chart ---
with tab1:
    st.subheader("Key Figures")

    if df_gaza_daily is not None and df_westbank_daily is not None:
        df_combined = pd.concat([df_gaza_daily, df_westbank_daily], ignore_index=True)
        
        # Aggregate totals
        total_attacked_seeking_aid = df_combined['aid_seeker_killed'].sum()
        total_injured = df_combined['injured'].sum()
        total_children_killed = df_combined['children_killed'].sum()
        total_starved = df_combined['starved'].sum()
        total_women_killed = df_combined['women_killed'].sum()
        total_medical_personnel_killed = df_combined['medical_killed'].sum()
        total_journalists_killed = df_combined['journalists_killed'].sum()
        total_first_responders_killed = df_combined['first_responders_killed'].sum()
        total_settler_attacks = df_combined['settler_attacks'].sum()

        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)
        col7, col8 = st.columns(2)
        
        col1.metric("Attacked Seeking Aid", f"{total_attacked_seeking_aid:,}")
        col2.metric("Injured", f"{total_injured:,}")
        col3.metric("Children Killed", f"{total_children_killed:,}")
        col4.metric("Starved to Death", f"{total_starved:,}")
        col5.metric("Women Killed", f"{total_women_killed:,}")
        col6.metric("Medical Personnel Killed", f"{total_medical_personnel_killed:,}")
        col7.metric("Journalists Killed", f"{total_journalists_killed:,}")
        col8.metric("First Responders Killed", f"{total_first_responders_killed:,}")
        st.markdown(f"**Settler Attacks:** {total_settler_attacks:,}")
        
        st.markdown("---")  # separator

        # --- Daily casualties chart ---
        df_combined = df_combined.sort_values('date')
        min_date = df_combined['date'].min()
        max_date = df_combined['date'].max()
        start_date, end_date = st.slider(
            "Select Date Range",
            min_value=min_date.date(),
            max_value=max_date.date(),
            value=(min_date.date(), max_date.date())
        )
        
        mask = (df_combined['date'].dt.date >= start_date) & (df_combined['date'].dt.date <= end_date)
        df_filtered = df_combined[mask]
        
        fig = px.line(
            df_filtered,
            x='date',
            y='killed',
            color='region',
            title=f"Daily Casualties ({start_date} to {end_date})",
            template="plotly_dark" if theme=="Dark" else "plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload Daily Gaza and West Bank CSVs.")

# --- Tab 2: Download Datasets ---
with tab2:
    st.subheader("Download All Datasets")
    
    def download_buttons(df, name):
        csv = df.to_csv(index=False).encode('utf-8-sig')
        json_data = df.to_json(orient='records', force_ascii=False).encode('utf-8')
        st.download_button(f"Download {name} as CSV", csv, f"{name}.csv", "text/csv")
        st.download_button(f"Download {name} as JSON", json_data, f"{name}.json", "application/json")

    if df_gaza_daily is not None:
        download_buttons(df_gaza_daily, "daily_gaza")
    if df_westbank_daily is not None:
        download_buttons(df_westbank_daily, "daily_westbank")
