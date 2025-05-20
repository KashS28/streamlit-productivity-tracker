import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Constants ---
TASKS = ["LinkedIn Connects", "Job Applications", "Leetcode Practice"]
TASK_TARGETS = {"LinkedIn Connects": 50, "Job Applications": 50, "Leetcode Practice": 5}
PROGRESS_FILE = "daily_progress.xlsx"

# --- Excel Setup ---
def initialize_excel():
    if not os.path.exists(PROGRESS_FILE):
        df = pd.DataFrame(columns=["Date"] + TASKS)
        df.to_excel(PROGRESS_FILE, index=False)

def load_today_progress():
    today = datetime.now().strftime('%Y-%m-%d')
    df = pd.read_excel(PROGRESS_FILE)
    if today not in df["Date"].values:
        new_row = pd.DataFrame([[today, 0, 0, 0]], columns=["Date"] + TASKS)
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(PROGRESS_FILE, index=False)
    return df, today

def save_progress(df):
    df.to_excel(PROGRESS_FILE, index=False)

# --- Streamlit Config ---
st.set_page_config("Productivity Tracker", layout="centered")
st.markdown("<h1 style='text-align: center;'>🚀 Daily Productivity Tracker</h1>", unsafe_allow_html=True)

initialize_excel()
df, today = load_today_progress()

# --- Session State ---
if "task_index" not in st.session_state:
    st.session_state.task_index = 0
if "count" not in st.session_state:
    current_task = TASKS[st.session_state.task_index]
    st.session_state.count = df[df["Date"] == today][current_task].values[0]

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 Tracker", "📈 Data"])

with tab1:
    current_task = TASKS[st.session_state.task_index]
    target = TASK_TARGETS[current_task]

    # Title + Metric
    st.markdown(f"<h3 style='text-align: center;'>Task: {current_task}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>Progress: {st.session_state.count} / {target}</h4>", unsafe_allow_html=True)

    # Centered Big Button using Streamlit native + CSS
    button_container = st.container()
    with button_container:
        st.markdown(
            """
            <style>
                div.stButton > button {
                    display: block;
                    margin: 20px auto;
                    font-size: 26px !important;
                    padding: 20px 50px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 12px;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        if st.button("➕ Add 1"):
            if st.session_state.count < target:
                st.session_state.count += 1
                df.loc[df["Date"] == today, current_task] = st.session_state.count
                save_progress(df)
            if st.session_state.count == target:
                st.success(f"🎉 YAYYY!! {current_task.upper()} DONE FOR THE DAY.")

    # Navigation Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏮ Go Back") and st.session_state.task_index > 0:
            st.session_state.task_index -= 1
            prev_task = TASKS[st.session_state.task_index]
            st.session_state.count = df[df["Date"] == today][prev_task].values[0]
    with col2:
        if st.button("⏭ Skip") and st.session_state.task_index < len(TASKS) - 1:
            st.session_state.task_index += 1
            next_task = TASKS[st.session_state.task_index]
            st.session_state.count = df[df["Date"] == today][next_task].values[0]

    st.caption("Progress resets automatically each new day.")

with tab2:
    st.subheader("📊 Daily Progress Data")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)

    with open(PROGRESS_FILE, "rb") as f:
        st.download_button("📥 Download Progress Sheet", f, file_name="daily_progress.xlsx")
