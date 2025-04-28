import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import time

# --- Helper Functions ---

def load_timetable():
    if os.path.exists("timetable.json"):
        with open("timetable.json", "r") as file:
            return json.load(file)
    else:
        return {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

def save_timetable(timetable):
    with open("timetable.json", "w") as file:
        json.dump(timetable, file, indent=4)

def parse_time_format(time_str):
    try:
        return datetime.strptime(time_str, "%H:%M")
    except ValueError:
        try:
            return datetime.strptime(time_str, "%I:%M %p")
        except ValueError:
            try:
                return datetime.strptime(time_str, "%I:%M%p")
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}. Use 24h (13:00) or 12h (1:00 PM)")

def calculate_duration(start_time, end_time):
    start = parse_time_format(start_time)
    end = parse_time_format(end_time)
    return end - start

def add_session(timetable, day, subject, start_time, end_time):
    timetable[day].append([subject, start_time, end_time])
    save_timetable(timetable)
    st.session_state.timetable = timetable

def edit_session(timetable, day, index, new_subject, new_start_time, new_end_time):
    timetable[day][index] = [new_subject, new_start_time, new_end_time]
    save_timetable(timetable)
    st.session_state.timetable = timetable

def delete_session(timetable, day, index):
    timetable[day].pop(index)
    save_timetable(timetable)
    st.session_state.timetable = timetable

def export_to_excel(timetable):
    rows = []
    for day, sessions in timetable.items():
        for session in sessions:
            rows.append({"Day": day, "Subject": session[0], "Start Time": session[1], "End Time": session[2]})
    df = pd.DataFrame(rows)
    df.to_excel("timetable.xlsx", index=False)

def get_current_and_next_class(timetable):
    now = datetime.now()
    current_day = now.strftime("%A")
    current_time = now.strftime("%H:%M")

    today_sessions = timetable.get(current_day, [])

    current_class = None
    next_class = None
    pre_notify_class = None

    for session in today_sessions:
        if len(session) < 3:
            continue

        subject, start_time, end_time = session

        try:
            start = parse_time_format(start_time).replace(year=now.year, month=now.month, day=now.day)
            end = parse_time_format(end_time).replace(year=now.year, month=now.month, day=now.day)

            if end < start:
                end += timedelta(days=1)

            if start <= now <= end:
                current_class = session

            time_to_start = start - now
            if timedelta(seconds=0) <= time_to_start <= timedelta(minutes=1):
                pre_notify_class = session

            elif start > now and (next_class is None or parse_time_format(next_class[1]).replace(year=now.year, month=now.month, day=now.day) > start):
                next_class = session

        except ValueError:
            continue

    if pre_notify_class:
        return "pre_notify", pre_notify_class[0], pre_notify_class[1], pre_notify_class[2], current_class
    elif current_class:
        return "current", current_class[0], current_class[1], current_class[2], current_class
    elif next_class:
        return "next", next_class[0], next_class[1], next_class[2], None
    else:
        return "none", None, None, None, None

# --- Streamlit Page Config ---
st.set_page_config(page_title="Timetable Manager", layout="wide")

# --- Sidebar ---
st.sidebar.title("📅 Timetable Manager")
timetable = load_timetable()

st.sidebar.subheader("➕ Add Session")
day = st.sidebar.selectbox("Select Day", list(timetable.keys()))
subject = st.sidebar.text_input("Subject")
start_time = st.sidebar.text_input("Start Time (24h: 13:00 or 12h: 1:00 PM)")
end_time = st.sidebar.text_input("End Time (24h: 14:00 or 12h: 2:00 PM)")

if st.sidebar.button("➕ Add"):
    if subject and start_time and end_time:
        try:
            parse_time_format(start_time)
            parse_time_format(end_time)
            add_session(timetable, day, subject, start_time, end_time)
            st.sidebar.success(f"Session for {subject} added!")
        except ValueError:
            st.sidebar.error("Invalid time format! Use 24h (13:00) or 12h (1:00 PM)")
    else:
        st.sidebar.warning("Fill all fields to add session.")

if st.sidebar.button("⬇️ Export Timetable to Excel"):
    export_to_excel(timetable)
    st.sidebar.success("Timetable exported as timetable.xlsx!")

# --- Dark Mode Toggle ---
dark_mode = st.sidebar.checkbox("🌙 Dark Mode")
if dark_mode:
    st.markdown("""
    <style>
    body, .stApp {
        background-color: #1e1e1e;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #2c2c2c;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Search ---
search_query = st.sidebar.text_input("🔍 Search Subject")

# --- Main Area ---
def display_timetable(timetable, search_query=""):
    st.title("📚 Your Timetable")

    found_subject = False

    for day, sessions in timetable.items():
        if sessions:
            st.header(day)
            for index, item in enumerate(sessions):
                if search_query.lower() in item[0].lower() or not search_query:
                    found_subject = True
                    try:
                        duration = calculate_duration(item[1], item[2])
                        st.write(f"📖 **{item[0]}** | 🕘 {item[1]} ➡️ {item[2]} | ⏳ Duration: {duration}")
                    except ValueError:
                        st.write(f"📖 **{item[0]}** | 🕘 {item[1]} ➡️ {item[2]} (Invalid time format!)")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ Edit {item[0]}", key=f"edit_{day}_{index}"):
                            with st.form(f"edit_form_{day}_{index}", clear_on_submit=True):
                                new_subject = st.text_input("New Subject", value=item[0])
                                new_start_time = st.text_input("New Start Time", value=item[1])
                                new_end_time = st.text_input("New End Time", value=item[2])
                                submitted = st.form_submit_button("Save Changes")
                                if submitted:
                                    try:
                                        parse_time_format(new_start_time)
                                        parse_time_format(new_end_time)
                                        edit_session(timetable, day, index, new_subject, new_start_time, new_end_time)
                                        st.success("Session updated!")
                                    except ValueError:
                                        st.error("Invalid time format!")

                    with col2:
                        if st.button(f"🗑️ Delete {item[0]}", key=f"delete_{day}_{index}"):
                            delete_session(timetable, day, index)
                            st.success("Session deleted!")

    if search_query and not found_subject:
        st.warning("No matching subject found.")

# Display
display_timetable(timetable, search_query)

# --- Auto-Refresh ---
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 30:
    st.session_state.last_refresh = time.time()
    st.rerun()

# --- Notifications ---
notification_placeholder = st.empty()
current_class_placeholder = st.empty()

status, subject, start_time, end_time, current_class = get_current_and_next_class(timetable)

def blinking_effect(message, is_pre_notify=False):
    for _ in range(2):  # Blink twice (safer UX)
        notification_placeholder.markdown(
            f"<div style='background-color: {'#FFA500' if is_pre_notify else '#32CD32'}; color: white; padding: 10px; font-size: 16px; border-radius: 5px; text-align: center;'>{message}</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.5)
        notification_placeholder.markdown("", unsafe_allow_html=True)
        time.sleep(0.5)

if current_class:
    current_class_placeholder.success(f"✅ Current Class: **{current_class[0]}** | 🕘 {current_class[1]} ➡️ {current_class[2]}")

if status == "pre_notify":
    message = f"⚠️ Class starting soon: **{subject}** | 🕘 {start_time} ➡️ {end_time}"
    blinking_effect(message, is_pre_notify=True)

elif status == "current":
    blinking_effect(f"✅ Current Class: **{subject}** | 🕘 {start_time} ➡️ {end_time}")

elif status == "next":
    notification_placeholder.info(f"⏭️ Next Class: **{subject}** | 🕘 {start_time} ➡️ {end_time}")

else:
    if not current_class:
        notification_placeholder.info("📚 No classes at the moment.")

