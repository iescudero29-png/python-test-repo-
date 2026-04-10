import streamlit as st
import time
import json
import os
from datetime import date, timedelta
import pandas as pd

st.set_page_config(page_title="Gym Tracker", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0a0a0a; }
    .block-container { padding: 2rem 4rem; max-width: 100%; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111111; border-radius: 12px; padding: 4px; gap: 4px; border: 0.5px solid #1a1a1a; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; color: #555555; border-radius: 8px; font-size: 13px; font-weight: 500; padding: 8px 24px; letter-spacing: 0.04em; }
    .stTabs [aria-selected="true"] { background-color: #1a0a0a; color: #c41e1e; }
    .stButton>button { background-color: #8b1a1a; color: #ffffff; border: none; font-weight: 600; width: 100%; border-radius: 10px; padding: 0.6rem 1rem; }
    .stButton>button:hover { background-color: #c41e1e; }
    .stTextInput>div>input, .stNumberInput>div>input, .stSelectbox>div>div { background-color: #111111; color: white; border: 0.5px solid #1a1a1a; border-radius: 10px; }
    .stSlider [data-baseweb="slider"] [role="slider"] { background-color: #8b1a1a !important; }
    .stSlider [data-baseweb="slider"] div[data-testid="stSliderTrackFill"] { background-color: #8b1a1a !important; }
    label { color: #999999 !important; font-size: 11px !important; letter-spacing: 0.08em; text-transform: uppercase; }
    h1 { color: white !important; font-weight: 600 !important; font-size: 28px !important; }
    h2 { color: white !important; font-weight: 500 !important; font-size: 18px !important; }
    h3 { color: #c41e1e !important; font-weight: 600 !important; font-size: 11px !important; letter-spacing: 0.1em; text-transform: uppercase; }
    p { color: #999999; font-size: 14px; }
    .stAlert { background-color: #0f1a0a; border: 0.5px solid #166534; color: #86efac; border-radius: 10px; }
    div[data-testid="metric-container"] { background-color: #111111; border: 0.5px solid #1a1a1a; border-radius: 12px; padding: 1.2rem; }
    div[data-testid="metric-container"] label { color: #555555 !important; font-size: 10px !important; }
    div[data-testid="metric-container"] [data-testid="metric-value"] { color: white !important; font-size: 24px !important; font-weight: 600 !important; }
    hr { border-color: #1a1a1a !important; }
    .stProgress > div > div { background-color: #8b1a1a; }
    </style>
""", unsafe_allow_html=True)

# daily motivational quotes
QUOTES = [
    "Show up even when you don't feel like it.",
    "Progress, not perfection.",
    "Every rep counts.",
    "Trust the process.",
    "One more set.",
    "Your only competition is yesterday's you.",
    "Discipline beats motivation every time.",
]

DATA_FILE = "gym_data.json"

# default data structure if no save file exists yet
DEFAULT_DATA = {
    "history": {},
    "prs": {},
    "exercise_db": [
        "Bench press", "Incline bench press", "Shoulder press",
        "Tricep pushdown", "Lateral raise", "Chest fly",
        "Pull up", "Lat pulldown", "Barbell row", "Bicep curl",
        "Squat", "Romanian deadlift", "Leg press", "Leg curl",
        "Hip thrust", "Calf raise", "Face pull", "Rear delt fly"
    ],
    "bodyweight": {},
    "streaks": {"last_date": "", "count": 0},
    "custom_split": ["Push", "Pull", "Legs", "Rest"]
}

# reads save file, returns default if file doesn't exist
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

# writes current data to save file
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# epley formula — estimates 1 rep max from weight and reps
def calc_1rm(weight, reps):
    return round(weight * (1 + reps / 30), 1)

# returns current streak, 0 if more than a day has passed
def get_streak(data):
    today_str = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))
    streaks = data.get("streaks", {"last_date": "", "count": 0})
    return streaks["count"] if streaks["last_date"] in [today_str, yesterday] else 0

# adds 1 to streak if first log of the day, resets if a day was missed
def update_streak(data):
    today_str = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))
    streaks = data.get("streaks", {"last_date": "", "count": 0})
    if streaks["last_date"] == today_str:
        pass
    elif streaks["last_date"] == yesterday:
        streaks["count"] += 1
        streaks["last_date"] = today_str
    else:
        streaks["count"] = 1
        streaks["last_date"] = today_str
    data["streaks"] = streaks
    return data

# load data and add any missing keys from newer versions
data = load_data()
for key, val in DEFAULT_DATA.items():
    if key not in data:
        data[key] = val
        save_data(data)

today = str(date.today())

# wipe today's log if it's a new day
if "last_date" not in st.session_state:
    st.session_state.last_date = today
if st.session_state.last_date != today:
    st.session_state.log = []
    st.session_state.last_date = today

# set up session state variables on first load
if "log" not in st.session_state:
    st.session_state.log = []
if "prs" not in st.session_state:
    st.session_state.prs = data.get("prs", {})
if "exercise_db" not in st.session_state:
    st.session_state.exercise_db = data.get("exercise_db", [])

# picks same quote all day, different one each new day
daily_quote = QUOTES[date.today().toordinal() % len(QUOTES)]

# week start is always monday
week_start = date.today() - timedelta(days=date.today().weekday())
week_data = {k: v for k, v in data["history"].items() if k >= str(week_start)}

# creates the 3 tabs
dashboard, workout, tools = st.tabs(["Dashboard", "Workout", "Tools"])

# ---- DASHBOARD ----
with dashboard:
    # header with streak
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.title("Gym Tracker")
        st.caption(date.today().strftime("%A, %B %d · %Y"))
        st.markdown(f"*{daily_quote}*")
    with col_right:
        st.metric("Streak", f"{get_streak(data)} days 🔥")

    st.divider()

    # four stat cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Today's sets", sum(e["sets"] for e in st.session_state.log))
    col2.metric("Exercises today", len(set(e["exercise"] for e in st.session_state.log)))
    col3.metric("Sessions this week", len(week_data))
    col4.metric("Sets this week", sum(e["sets"] for entries in week_data.values() for e in entries))

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("TODAY'S SPLIT")
        # hidden edit form, shows when clicked
        with st.expander("Edit split"):
            split_input = st.text_input("Days (comma separated)", value=", ".join(data["custom_split"]))
            if st.button("Save split"):
                new_split = [s.strip() for s in split_input.split(",") if s.strip()]
                if new_split:
                    data["custom_split"] = new_split
                    save_data(data)
                    st.success("Saved!")
                    st.rerun()
        st.session_state.split = st.select_slider("Today", options=data["custom_split"])

    with col_b:
        st.subheader("WARMUP CHECKLIST")
        # shows success only when all four are checked
        w1 = st.checkbox("5 min cardio")
        w2 = st.checkbox("Dynamic stretching")
        w3 = st.checkbox("Activation sets")
        w4 = st.checkbox("Joint mobility")
        if all([w1, w2, w3, w4]):
            st.success("Warmup done. Time to work.")

    st.divider()

    # this week's best weight per exercise as metric cards
    st.subheader("THIS WEEK'S BEST LIFTS")
    if week_data:
        week_prs = {}
        for entries in week_data.values():
            for e in entries:
                if e["exercise"] not in week_prs or e["weight"] > week_prs[e["exercise"]]:
                    week_prs[e["exercise"]] = e["weight"]
        cols = st.columns(4)
        for i, (ex, w) in enumerate(week_prs.items()):
            cols[i % 4].metric(ex, f"{w} lbs")
    else:
        st.caption("Nothing logged this week yet.")

# ---- WORKOUT ----
with workout:
    col_left, col_right = st.columns(2)

    with col_left:
        st.title("Log workout")
        st.caption(date.today().strftime("%A, %B %d"))
        st.divider()

        st.subheader("EXERCISE")
        # searchable dropdown from saved exercise database
        exercise_name = st.selectbox("Select exercise", sorted(st.session_state.exercise_db))

        # find last session's numbers for this exercise
        last_weights = []
        for day, entries in sorted(data["history"].items(), reverse=True):
            if day != today:
                last_weights = [e for e in entries if e["exercise"] == exercise_name]
                if last_weights:
                    break
        if last_weights:
            best_last = max(last_weights, key=lambda x: x["weight"])
            st.caption(f"Last session → {best_last['weight']}lbs · {best_last['sets']} sets × {best_last['reps']} reps")

        # three inputs side by side
        col1, col2, col3 = st.columns(3)
        with col1:
            weight = st.number_input("Weight (lbs)", min_value=0)
        with col2:
            sets = st.number_input("Sets", min_value=0)
        with col3:
            reps = st.number_input("Reps", min_value=0)

        # live 1rm estimate as you type
        if weight > 0 and reps > 0:
            st.caption(f"Estimated 1RM → {calc_1rm(weight, reps)} lbs")

        session_note = st.text_input("Note", placeholder="Felt strong, good sleep...")

        if st.button("Log set"):
            if exercise_name:
                # block duplicate weight on same exercise
                duplicate = next((e for e in st.session_state.log
                                 if e["exercise"] == exercise_name and e["weight"] == weight), None)
                if duplicate:
                    st.warning(f"Already logged {weight}lbs on {exercise_name}.")
                else:
                    entry = {"exercise": exercise_name, "weight": weight, "sets": sets, "reps": reps, "note": session_note}
                    st.session_state.log.append(entry)
                    # save to history file
                    if today not in data["history"]:
                        data["history"][today] = []
                    data["history"][today].append(entry)
                    # check if new PR
                    if exercise_name not in st.session_state.prs or weight > st.session_state.prs[exercise_name]:
                        prev = st.session_state.prs.get(exercise_name, 0)
                        st.session_state.prs[exercise_name] = weight
                        data["prs"][exercise_name] = weight
                        if prev > 0:
                            st.success(f"★ New PR — {weight}lbs on {exercise_name}. Up {weight - prev}lbs.")
                    data = update_streak(data)
                    save_data(data)

        st.divider()
        st.subheader("MANAGE DATABASE")
        # add new exercise to the searchable list
        new_ex = st.text_input("Add exercise")
        if st.button("Add to database"):
            if new_ex and new_ex not in st.session_state.exercise_db:
                st.session_state.exercise_db.append(new_ex)
                data["exercise_db"] = st.session_state.exercise_db
                save_data(data)
                st.success(f"Added {new_ex}!")
            elif new_ex in st.session_state.exercise_db:
                st.warning("Already in your database.")

        # remove exercise from the list
        exercise_to_delete = st.selectbox("Remove exercise", sorted(st.session_state.exercise_db), key="delete_ex")
        if st.button("Remove from database"):
            st.session_state.exercise_db.remove(exercise_to_delete)
            data["exercise_db"] = st.session_state.exercise_db
            save_data(data)
            st.success(f"Removed {exercise_to_delete}!")
            st.rerun()

    with col_right:
        st.title("Today's log")
        st.caption(date.today().strftime("%A, %B %d"))
        st.divider()

        if st.session_state.log:
            for i, entry in enumerate(st.session_state.log):
                # red dot if PR, white if normal
                is_pr = entry["exercise"] in st.session_state.prs and entry["weight"] == st.session_state.prs[entry["exercise"]]
                c1, c2 = st.columns([4, 1])
                with c1:
                    tag = "★ " if is_pr else ""
                    st.markdown(f"{'🔴' if is_pr else '⚪'} **{tag}{entry['exercise']}** — {entry['weight']}lbs · {entry['sets']} sets · {entry['reps']} reps")
                    if entry.get("note"):
                        st.caption(entry["note"])
                with c2:
                    # unique key required for each button in a loop
                    if st.button("✕", key=f"del_{i}"):
                        st.session_state.log.pop(i)
                        st.rerun()
            if len(set(e["exercise"] for e in st.session_state.log)) >= 3:
                st.success("Solid session. 3+ exercises logged 💪")
        else:
            st.caption("Nothing logged yet.")

        st.divider()
        st.subheader("ALL TIME PRS")
        if st.session_state.prs:
            pr_cols = st.columns(2)
            for i, (ex, w) in enumerate(st.session_state.prs.items()):
                pr_cols[i % 2].metric(ex, f"{w} lbs")
        else:
            st.caption("No PRs yet.")

# ---- TOOLS ----
with tools:
    st.title("Tools")
    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("REST TIMER")
        rest_time = st.select_slider("Duration", options=[30, 60, 90, 120, 180], value=90)
        progress_bar = st.progress(0)
        if st.button("Start timer"):
            timer_placeholder = st.empty()
            # counts down one second at a time
            for i in range(rest_time, 0, -1):
                mins = i // 60
                secs = i % 60
                timer_placeholder.markdown(f"## {mins}:{secs:02d}")
                progress_bar.progress((rest_time - i) / rest_time)
                time.sleep(1)
            timer_placeholder.markdown("## Done.")
            progress_bar.progress(1.0)

    with col_right:
        st.subheader("1RM CALCULATOR")
        c1, c2 = st.columns(2)
        with c1:
            calc_weight = st.number_input("Weight lifted", min_value=0)
        with c2:
            calc_reps = st.number_input("Reps performed", min_value=0)
        if calc_weight > 0 and calc_reps > 0:
            st.metric("Estimated 1RM", f"{calc_1rm(calc_weight, calc_reps)} lbs")