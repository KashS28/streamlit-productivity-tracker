import streamlit as st
import streamlit_authenticator as stauth
import yaml
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from yaml.loader import SafeLoader

# --- Load Auth Config ---
with open("productivity-tracker/config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    "tracker_cookie",
    "random_key",
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login(name="Login", location="main")


if authentication_status is False:
    st.error("Incorrect username or password")
elif authentication_status is None:
    st.warning("Please enter your login details")
elif authentication_status:

    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

    # --- Constants ---
    BASE_TASKS = {
        "LinkedIn Connects": 50,
        "Job Applications": 50,
        "Leetcode Practice": 5
    }
    USER_DATA_PATH = f"data/data_{username}.xlsx"
    os.makedirs("data", exist_ok=True)

    # --- Session State Init ---
    if "custom_tasks" not in st.session_state:
        st.session_state.custom_tasks = {}
    if "hidden_tasks" not in st.session_state:
        st.session_state.hidden_tasks = []
    if "task_index" not in st.session_state:
        st.session_state.task_index = 0

    def get_all_tasks():
        base = BASE_TASKS.copy()
        base.update(st.session_state.custom_tasks)
        return base

    def initialize_excel(tasks):
        if not os.path.exists(USER_DATA_PATH):
            df = pd.DataFrame(columns=["Date"] + list(tasks.keys()))
            df.to_excel(USER_DATA_PATH, index=False)
        else:
            df = pd.read_excel(USER_DATA_PATH)
            for task in tasks:
                if task not in df.columns:
                    df[task] = 0
            df.to_excel(USER_DATA_PATH, index=False)

    def load_today_progress(tasks):
        today = datetime.now().strftime('%Y-%m-%d')
        df = pd.read_excel(USER_DATA_PATH)
        if today not in df["Date"].values:
            new_row = pd.DataFrame([[today] + [0] * len(tasks)], columns=["Date"] + list(tasks.keys()))
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(USER_DATA_PATH, index=False)
        return df, today

    def save_progress(df):
        df.to_excel(USER_DATA_PATH, index=False)

    def get_weekly_chart_data(tasks):
        df = pd.read_excel(USER_DATA_PATH)
        df["Date"] = pd.to_datetime(df["Date"])
        recent = df[df["Date"] >= datetime.now() - timedelta(days=6)]
        return recent[["Date"] + tasks]

    # --- Task Data ---
    all_tasks = get_all_tasks()
    initialize_excel(all_tasks)
    df, today = load_today_progress(all_tasks)
    visible_tasks = [t for t in all_tasks if t not in st.session_state.hidden_tasks]
    task_list = visible_tasks

    # --- Sidebar ---
    st.sidebar.title("📌 Your Tasks")
    for i, task in enumerate(task_list):
        if st.sidebar.button(task):
            st.session_state.task_index = i

    st.sidebar.markdown("---")
    st.sidebar.header("➕ Add Task")
    task_name = st.sidebar.text_input("Task Name")
    task_target = st.sidebar.number_input("Target", min_value=1, step=1)
    if st.sidebar.button("Add Task"):
        if task_name and task_name not in all_tasks:
            st.session_state.custom_tasks[task_name] = int(task_target)
            st.success(f"Added '{task_name}' with target {task_target}. Please refresh.")
            st.rerun()

    if task_list:
        current_task = task_list[st.session_state.task_index]
        target = all_tasks[current_task]
        current_value = df[df["Date"] == today][current_task].values[0]

        st.sidebar.subheader(f"⚙️ {current_task} Settings")
        if st.sidebar.button("🔄 Reset Today"):
            df.loc[df["Date"] == today, current_task] = 0
            save_progress(df)
            st.rerun()
        if st.sidebar.button("🗑 Hide Task"):
            st.session_state.hidden_tasks.append(current_task)
            st.rerun()

    # --- Main Tabs ---
    tab1, tab2 = st.tabs(["📋 Tracker", "📈 Data"])

    with tab1:
        if task_list:
            current_task = task_list[st.session_state.task_index]
            target = all_tasks[current_task]
            current_value = df[df["Date"] == today][current_task].values[0]

            st.header(f"📍 Task: {current_task}")
            st.metric("Today's Progress", f"{current_value} / {target}")
            st.progress(min(current_value / target, 1.0))

            st.markdown("""
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
            """, unsafe_allow_html=True)

            if st.button("➕ Add 1"):
                if current_value < target:
                    df.loc[df["Date"] == today, current_task] = current_value + 1
                    save_progress(df)
                    current_value += 1
                if current_value == target:
                    st.balloons()
                    st.snow()
                    st.success(f"🎉 YAYYY!! {current_task.upper()} DONE FOR THE DAY.")
                st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⏮ Go Back") and st.session_state.task_index > 0:
                    st.session_state.task_index -= 1
                    st.rerun()
            with col2:
                if st.button("⏭ Skip") and st.session_state.task_index < len(task_list) - 1:
                    st.session_state.task_index += 1
                    st.rerun()

    with tab2:
        st.subheader("📊 Weekly Progress Chart")
        if visible_tasks:
            chart_data = get_weekly_chart_data(visible_tasks)
            chart_data_grouped = chart_data.groupby("Date").sum().reset_index()

            fig, ax = plt.subplots(figsize=(10, 5))
            for task in visible_tasks:
                ax.plot(chart_data_grouped["Date"], chart_data_grouped[task], marker='o', label=task)
            ax.set_ylabel("Count")
            ax.set_xlabel("Date")
            ax.set_title("Weekly Task Progress")
            ax.legend()
            st.pyplot(fig)

        st.subheader("📅 Full Daily Log")
        st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)

        with open(USER_DATA_PATH, "rb") as f:
            st.download_button("📥 Download Excel", f, file_name=f"{username}_progress.xlsx")
