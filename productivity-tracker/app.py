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

# --- Streamlit Setup ---
st.set_page_config("Productivity Tracker", layout="centered")
st.title("🚀 Daily Productivity Tracker")

initialize_excel()
df, today = load_today_progress()

# --- Session State ---
if "task_index" not in st.session_state:
    st.session_state.task_index = 0
if "count" not in st.session_state:
    task = TASKS[st.session_state.task_index]
    st.session_state.count = df[df["Date"] == today][task].values[0]

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 Tracker", "📈 Data"])

with tab1:
    task = TASKS[st.session_state.task_index]
    target = TASK_TARGETS[task]

    st.subheader(f"Task: {task}")
    st.metric("Today's Progress", f"{st.session_state.count} / {target}")

    # --- Huge Centered Button ---
    st.markdown(
        """
        <div style="display: flex; justify-content: center; margin: 30px 0;">
            <form action="?add=true">
                <button style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px 50px;
                    font-size: 28px;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                " type="submit">➕ Add 1</button>
            </form>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Handle Increment via Query Param ---
    if st.query_params.get("add") == "true":
        if st.session_state.count < target:
            st.session_state.count += 1
            df.loc[df["Date"] == today, task] = st.session_state.count
            save_progress(df)
        if st.session_state.count == target:
            st.success(f"🎉 YAYYY!! {task.upper()} DONE FOR THE DAY.")
        st.query_params.clear()  # Reset params after use

    # --- Navigation Buttons ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏮ Go Back") and st.session_state.task_index > 0:
            st.session_state.task_index -= 1
            task = TASKS[st.session_state.task_index]
            st.session_state.count = df[df["Date"] == today][task].values[0]
    with col2:
        if st.button("⏭ Skip") and st.session_state.task_index < len(TASKS) - 1:
            st.session_state.task_index += 1
            task = TASKS[st.session_state.task_index]
            st.session_state.count = df[df["Date"] == today][task].values[0]

    st.caption("Progress resets automatically each new day.")

with tab2:
    st.subheader("📊 Daily Progress Data")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)

    with open(PROGRESS_FILE, "rb") as f:
        st.download_button("📥 Download Progress Sheet", f, file_name="daily_progress.xlsx")
