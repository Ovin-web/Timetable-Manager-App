import streamlit as st
from streamlit_autorefresh import st_autorefresh
import json
import datetime

# 🔁 Auto-refresh every 10 seconds
st_autorefresh(interval=10 * 1000, key="refresh")

# 📁 Load data
def load_data():
    try:
        with open("timetable.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# 💾 Save data
def save_data(data):
    with open("timetable.json", "w") as f:
        json.dump(data, f, indent=4)

# 📆 Get next session based on current time
def get_next_session(data):
    now = datetime.datetime.now().strftime("%A %H:%M")
    for item in data:
        if item["day"] + " " + item["time"] > now:
            return item
    return None

# ✏️ Edit session
def edit_session(index, new_item):
    data = load_data()
    data[index] = new_item
    save_data(data)

# ❌ Delete session
def delete_session(index):
    data = load_data()
    data.pop(index)
    save_data(data)

# 🖼️ UI
st.set_page_config(page_title="Timetable Manager", layout="wide")
st.title("🗓️ Timetable Manager")

menu = ["View Timetable", "Add Session"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Session":
    st.subheader("Add a New Class Session")
    course = st.text_input("Course Name")
    day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    time = st.time_input("Time")
    location = st.text_input("Location")

    if st.button("Add Session"):
        new_entry = {
            "course": course,
            "day": day,
            "time": time.strftime("%H:%M"),
            "location": location
        }
        data = load_data()
        data.append(new_entry)
        save_data(data)
        st.success("✅ Session added!")

elif choice == "View Timetable":
    st.subheader("📅 Your Timetable")
    data = load_data()

    if data:
        for i, item in enumerate(data):
            st.write(f"📘 **{item['course']}** on **{item['day']}** at **{item['time']}** in *{item['location']}*")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit {i}", key=f"edit_{i}"):
                    with st.form(f"form_edit_{i}"):
                        new_course = st.text_input("Course Name", value=item['course'])
                        new_day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(item['day']))
                        new_time = st.time_input("Time", value=datetime.datetime.strptime(item['time'], "%H:%M").time())
                        new_location = st.text_input("Location", value=item['location'])
                        submitted = st.form_submit_button("Save Changes")
                        if submitted:
                            new_item = {
                                "course": new_course,
                                "day": new_day,
                                "time": new_time.strftime("%H:%M"),
                                "location": new_location
                            }
                            edit_session(i, new_item)
                            st.success("✅ Session updated!")
                            st.experimental_rerun()
            with col2:
                if st.button(f"Delete {i}", key=f"delete_{i}"):
                    delete_session(i)
                    st.warning("⚠️ Session deleted!")
                    st.experimental_rerun()

        st.markdown("---")
        next_session = get_next_session(data)
        if next_session:
            st.success(f"🎯 **Next Session**: {next_session['course']} on {next_session['day']} at {next_session['time']} in {next_session['location']}")
        else:
            st.info("✅ No upcoming sessions today.")
    else:
        st.info("ℹ️ No timetable data found. Add a session first.")

