import streamlit as st
import json
from datetime import datetime, timedelta
import pytz

# Load timetable
def load_timetable():
    try:
        with open("timetable.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save timetable
def save_timetable(timetable):
    with open("timetable.json", "w") as f:
        json.dump(timetable, f, indent=4)

# Convert to 24hr format
def convert_to_24hr_format(time_str):
    try:
        return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
    except ValueError:
        return time_str

# Determine current/next class
def get_current_and_next_class(timetable):
    tz = pytz.timezone("Africa/Dar_es_Salaam")
    now = datetime.now(tz)
    today = now.strftime("%A")
    current_time = now.strftime("%H:%M")

    current = None
    next_up = None

    if today in timetable:
        sorted_classes = sorted(timetable[today], key=lambda x: convert_to_24hr_format(x[1]))
        for i, (name, start, end) in enumerate(sorted_classes):
            start_24 = convert_to_24hr_format(start)
            end_24 = convert_to_24hr_format(end)

            if start_24 <= current_time <= end_24:
                current = (name, start, end)
            elif current_time < start_24:
                next_up = (name, start, end)
                break

    return current, next_up

# Streamlit app
st.set_page_config(page_title="Timetable Manager", layout="centered")
st.title("📅 Timetable Manager with Notifications")

# Reset notifications if needed
if 'notified' not in st.session_state:
    st.session_state['notified'] = False

# Menu and options
menu = ["View Timetable", "Add Class", "Edit Class", "Remove Class"]
choice = st.sidebar.selectbox("Menu", menu)

timetable = load_timetable()

# Display notifications only if not already shown
current, upcoming = get_current_and_next_class(timetable)
if current:
    if not st.session_state['notified']:  # Show the notification only once
        st.success(f"🟢 Current: {current[0]} ({current[1]} - {current[2]})")
        st.session_state['notified'] = True  # Set flag to prevent repeated notifications
elif upcoming:
    next_time = datetime.strptime(convert_to_24hr_format(upcoming[1]), "%H:%M") - timedelta(minutes=5)
    now_time = datetime.now(pytz.timezone("Africa/Dar_es_Salaam")).strftime("%H:%M")
    if now_time >= next_time.strftime("%H:%M"):
        if not st.session_state['notified']:
            st.warning(f"🔔 Next: {upcoming[0]} at {upcoming[1]} — starts in 5 mins")
            st.session_state['notified'] = True  # Set flag for next class notification
else:
    if not st.session_state['notified']:
        st.info("No upcoming or current classes right now.")
        st.session_state['notified'] = True  # Set flag for no current class

# View
if choice == "View Timetable":
    st.subheader("📋 Current Timetable")
    if timetable:
        for day, classes in timetable.items():
            st.write(f"### {day}")
            for cls in classes:
                st.write(f"- **{cls[0]}**: {cls[1]} - {cls[2]}")
    else:
        st.write("No classes added yet.")

# Add
elif choice == "Add Class":
    st.subheader("➕ Add New Class")
    with st.form("add_form"):
        day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        name = st.text_input("Class Name")
        start = st.text_input("Start Time (e.g. 09:00 AM or 14:00)")
        end = st.text_input("End Time (e.g. 10:00 AM or 15:00)")
        submitted = st.form_submit_button("Add")

        if submitted:
            if day in timetable:
                timetable[day].append([name, start, end])
            else:
                timetable[day] = [[name, start, end]]
            save_timetable(timetable)
            st.success("Class added successfully!")

# Edit
elif choice == "Edit Class":
    st.subheader("✏️ Edit Existing Class")
    day = st.selectbox("Select Day", list(timetable.keys()))
    class_list = timetable.get(day, [])
    if class_list:
        class_names = [cls[0] for cls in class_list]
        selected = st.selectbox("Select Class", class_names)
        cls_index = class_names.index(selected)
        with st.form("edit_form"):
            new_name = st.text_input("New Class Name", value=class_list[cls_index][0])
            new_start = st.text_input("New Start Time", value=class_list[cls_index][1])
            new_end = st.text_input("New End Time", value=class_list[cls_index][2])
            submitted = st.form_submit_button("Update")

            if submitted:
                timetable[day][cls_index] = [new_name, new_start, new_end]
                save_timetable(timetable)
                st.success("Class updated successfully!")
    else:
        st.warning("No classes found for that day.")

# Remove
elif choice == "Remove Class":
    st.subheader("❌ Remove a Class")
    day = st.selectbox("Select Day", list(timetable.keys()))
    class_list = timetable.get(day, [])
    if class_list:
        class_names = [cls[0] for cls in class_list]
        selected = st.selectbox("Select Class to Remove", class_names)
        if st.button("Remove Class"):
            timetable[day] = [cls for cls in class_list if cls[0] != selected]
            save_timetable(timetable)
            st.success(f"Class '{selected}' removed.")
    else:
        st.warning("No classes found for that day.")
